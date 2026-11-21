"""Route physical insulated jumpers in the breadboard's local metre coordinates."""

from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import pairwise
from math import isfinite
from operator import itemgetter


# All planar calculations use integer micrometres for stable obstacle boundaries.
UNITS_PER_METRE = 1_000_000
BODY_CLEARANCE = 1_000
TERMINAL_CLEARANCE = 1_700
WIRE_CLEARANCE = 1_900
FIRST_HEIGHT = 3_800
LAYER_SPACING = 2_200
BEND_COST = 3_000
CROSSING_COST = 28_000
BOARD_LANES = (0, -2_540, 2_540, -16_500, 16_500, -27_000, 27_000)


class RoutingError(ValueError):
    """A physical connection has no usable route in the supplied layout."""


@dataclass(frozen=True)
class Rect:
    """A horizontal exclusion area, including wire clearance."""

    low_x: int
    high_x: int
    low_z: int
    high_z: int

    def contains(self, point):
        x, z = point
        return self.low_x < x < self.high_x and self.low_z < z < self.high_z

    def blocks(self, start, end):
        (x1, z1), (x2, z2) = start, end
        return (
            min(x1, x2) < self.high_x and max(x1, x2) > self.low_x
            and min(z1, z2) < self.high_z and max(z1, z2) > self.low_z
        )


@dataclass(frozen=True)
class Obstacle:
    rect: Rect
    top: int


def metric_point(position):
    if isinstance(position, dict):
        position = itemgetter("x", "y", "z")(position)
    if not all(isfinite(value) for value in position):
        raise RoutingError("Route coordinates must be finite")
    return tuple(round(value * UNITS_PER_METRE) for value in position)


def projected(point):
    x, _, z = point
    return x, z


def position(point):
    return dict(zip(("x", "y", "z"), (value / UNITS_PER_METRE for value in point)))


def footprint(point, size, clearance):
    x, _, z = point
    dx, _, dz = size
    px = dx // 2 + clearance
    pz = dz // 2 + clearance
    return Rect(x - px, x + px, z - pz, z + pz)


def segment_area(start, end, clearance):
    (x1, z1), (x2, z2) = start, end
    return Rect(
        min(x1, x2) - clearance, max(x1, x2) + clearance,
        min(z1, z2) - clearance, max(z1, z2) + clearance,
    )


def compact(path):
    """Remove duplicate vertices and redundant collinear intermediate points."""
    result = []
    for point in path:
        if result and point == result[-1]:
            continue
        if len(result) >= 2:
            first, middle = result[-2:]
            changing = [axis for axis in range(len(point)) if first[axis] != middle[axis]]
            if len(changing) == 1:
                axis = changing[0]
                if all(middle[i] == point[i] for i in range(len(point)) if i != axis):
                    if (middle[axis] - first[axis]) * (point[axis] - middle[axis]) > 0:
                        result.pop()
        result.append(point)
    return result


def segment_length(start, end):
    return abs(start[0] - end[0]) + abs(start[1] - end[1])


def exit_terminal(point, component):
    """Leave an external header toward the nearest free side before rising."""
    x, y, z = point
    if component is None or not component.rect.contains((x, z)):
        return point
    if y + BODY_CLEARANCE >= component.top:
        return point
    area = component.rect
    candidates = [
        (area.low_x, y, z), (area.high_x, y, z),
        (x, y, area.low_z), (x, y, area.high_z),
    ]
    return min(candidates, key=lambda exit_point: segment_length(projected(point), projected(exit_point)))


def preferred_lanes(profile):
    if not hasattr(profile, "dimensions_m"):
        return BOARD_LANES
    half_depth = round(profile.dimensions_m["z"] * UNITS_PER_METRE / 2)
    rows = {row: metric_point(profile.hole(row + "1").position_m)[2]
            for row in ("A", "E", "F", "J", "TP", "TN", "BP", "BN")}
    return (
        (rows["E"] + rows["F"]) // 2,
        (rows["A"] + max(rows["TP"], rows["TN"])) // 2,
        (rows["J"] + min(rows["BP"], rows["BN"])) // 2,
        (min(rows["TP"], rows["TN"]) - half_depth) // 2,
        (max(rows["BP"], rows["BN"]) + half_depth) // 2,
    )


def route_candidates(start, end, obstacles, lanes):
    x1, z1 = start
    x2, z2 = end
    x_lanes = {(x1 + x2) // 2}
    z_lanes = {(z1 + z2) // 2, *lanes}
    for area in obstacles:
        x_lanes.update((area.low_x, area.high_x))
        z_lanes.update((area.low_z, area.high_z))
    yield [start, (x1, z2), end]
    yield [start, (x2, z1), end]
    for x in sorted(x_lanes, key=lambda value: (abs(value - (x1 + x2) // 2), value)):
        yield [start, (x, z1), (x, z2), end]
    for z in sorted(z_lanes, key=lambda value: (abs(value - (z1 + z2) // 2), value)):
        yield [start, (x1, z), (x2, z), end]


def choose_route(start, end, obstacles, previous, lanes):
    """Try straight paths and L- and Z-shaped lanes before searching more turns."""
    if start == end:
        return [start]

    def usable(segment):
        return not any(area.blocks(*segment) for area in obstacles)

    def cost(path):
        segments = list(pairwise(path))
        crossings = sum(any(area.blocks(*segment) for area in areas for segment in segments)
                        for _, areas in previous)
        return (sum(segment_length(*segment) for segment in segments)
                + BEND_COST * (len(segments) - 1) + CROSSING_COST * crossings)

    best = None
    best_cost = None
    for candidate in route_candidates(start, end, obstacles, lanes):
        candidate = compact(candidate)
        if not all(usable(segment) for segment in pairwise(candidate)):
            continue
        candidate_cost = cost(candidate)
        if best_cost is None or candidate_cost < best_cost:
            best, best_cost = candidate, candidate_cost
    if best is not None:
        return best
    return search_route(start, end, obstacles, previous, lanes)


def search_route(start, end, obstacles, previous, lanes):
    """Find a multi-turn route on the visibility grid when simple lanes are blocked."""
    xs = sorted({start[0], end[0], *(area.low_x for area in obstacles),
                 *(area.high_x for area in obstacles)})
    zs = sorted({start[1], end[1], *lanes, *(area.low_z for area in obstacles),
                 *(area.high_z for area in obstacles)})
    start_index = xs.index(start[0]), zs.index(start[1])
    end_index = xs.index(end[0]), zs.index(end[1])
    pending = [(0, 0, *start_index, 0)]
    costs = {(*start_index, 0): 0}
    parents = {}

    while pending:
        _, total, i, j, axis = heappop(pending)
        state = i, j, axis
        if total != costs[state]:
            continue
        if (i, j) == end_index:
            path = [(xs[i], zs[j])]
            while state in parents:
                state = parents[state]
                path.append((xs[state[0]], zs[state[1]]))
            return compact(path[::-1])

        first = xs[i], zs[j]
        for ni, nj, direction in ((i - 1, j, 1), (i + 1, j, 1), (i, j - 1, 2), (i, j + 1, 2)):
            if not 0 <= ni < len(xs) or not 0 <= nj < len(zs):
                continue
            second = xs[ni], zs[nj]
            if any(area.blocks(first, second) for area in obstacles):
                continue
            joined = ni, nj, direction
            bends = BEND_COST if axis and axis != direction else 0
            crossings = sum(any(area.blocks(first, second) for area in areas) for _, areas in previous)
            next_cost = total + segment_length(first, second) + bends + crossings * CROSSING_COST
            if joined in costs and costs[joined] <= next_cost:
                continue
            costs[joined] = next_cost
            parents[joined] = state
            heappush(pending, (next_cost + segment_length(second, end), next_cost, *joined))
    raise RoutingError("No corridor around the supplied footprints")


def connect_ends(first, start, path, end, last, height):
    raised = [(x, height, z) for x, z in path]
    # Preserve vertical insertion at board holes and the physical external connector position.
    return compact([first, start, *raised, end, last])


def route_wires(plan, parts, profile):
    """Return intermediate waypoints by physical wire ID, in board-local metres."""
    bodies = {}
    terminals = {}
    def add_terminals(name, position_m, size_m, pins):
        origin = metric_point(position_m)
        size = metric_point(size_m)
        bodies[name] = Obstacle(footprint(origin, size, BODY_CLEARANCE), origin[1] + size[1])
        for pin in pins:
            terminal = pin.get("terminal", f'{name}.{pin["id"]}')
            if terminal.startswith(name + "."):
                terminals[terminal] = metric_point(pin["position_m"])

    for component in plan["components"]:
        add_terminals(component["instance_id"], component["position_m"],
                      parts[component["part_id"]]["size_m"], component["pins"])
    for junction in plan.get("junctions", []):
        add_terminals(junction["id"], junction["position_m"], junction["size_m"], junction["ports"])

    wires = sorted(plan["connections"], key=itemgetter("id"))
    if len({wire["id"] for wire in wires}) != len(wires):
        raise RoutingError("Wire IDs must be unique")
    endpoints = {}
    exits = {}
    owners = {}
    for wire in wires:
        for terminal in (wire["from"], wire["to"]):
            if terminal in endpoints:
                continue
            if terminal in terminals:
                point = terminals[terminal]
                owner = terminal.split(".", 1)[0]
            else:
                try:
                    hole = profile.hole(terminal)
                except (KeyError, ValueError) as error:
                    raise RoutingError(f'{wire["id"]}: unknown terminal {terminal}') from error
                point = metric_point(hole.position_m)
                owner = None
            endpoints[terminal] = point
            owners[terminal] = owner
            exits[terminal] = exit_terminal(point, bodies.get(owner))

    result = {}
    previous = []
    lanes = preferred_lanes(profile)
    for wire in wires:
        first_name, last_name = wire["from"], wire["to"]
        first, last = endpoints[first_name], endpoints[last_name]
        start, end = exits[first_name], exits[last_name]
        planar_start, planar_end = projected(start), projected(end)
        base = max(FIRST_HEIGHT, first[1] + BODY_CLEARANCE, last[1] + BODY_CLEARANCE)
        for name, port in ((first_name, start), (last_name, end)):
            owner = bodies.get(owners[name])
            if owner and owner.rect.contains(projected(port)):
                base = max(base, owner.top + BODY_CLEARANCE)
        areas = [body.rect for body in bodies.values() if body.top + BODY_CLEARANCE > base]
        # Reserve vertical connector stems even for jumpers that are routed later.
        for name, port in exits.items():
            if name not in (first_name, last_name):
                point = projected(port)
                if point not in (planar_start, planar_end):
                    areas.append(segment_area(point, point, TERMINAL_CLEARANCE))
        for name, port in ((first_name, start), (last_name, end)):
            point = projected(port)
            if any(body.rect.contains(point) and body.top > port[1]
                   for owner, body in bodies.items() if owner != owners[name]):
                raise RoutingError(f'{wire["id"]}: terminal {name} is inside a component footprint')
        try:
            path = choose_route(planar_start, planar_end, areas, previous, lanes)
        except RoutingError as error:
            raise RoutingError(f'{wire["id"]}: {error}') from error

        segments = list(pairwise(path))
        occupied_heights = [
            height for height, reserved in previous
            if any(area.blocks(*segment) for area in reserved for segment in segments)
        ]
        height = base
        while any(abs(height - occupied) < LAYER_SPACING for occupied in occupied_heights):
            height += LAYER_SPACING
        route = connect_ends(first, start, path, end, last, height)
        if len(route) < 2:
            raise RoutingError(f'{wire["id"]}: distinct terminals occupy the same point')
        result[wire["id"]] = [position(point) for point in route[1:-1]]
        previous.append((height, [segment_area(*segment, WIRE_CLEARANCE) for segment in segments]))
    return result
