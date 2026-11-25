package org.mechavision.benchmark;

import android.app.Activity;
import android.app.Instrumentation;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Build;
import android.os.Bundle;
import android.os.Debug;
import android.os.SystemClock;

import ai.onnxruntime.OnnxTensor;
import ai.onnxruntime.OrtEnvironment;
import ai.onnxruntime.OrtSession;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.nio.FloatBuffer;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.Collections;

public final class Benchmark extends Instrumentation {
    private static final int SIDE = 256;
    private static final int INPUT_CAP = 960;
    private static final long MODEL_BYTES = 83084930;
    private static final String SHA256 = "7f9f5a8935b2eb22b3ee0245d34996063f54562df390d34714af2d76928695bc";
    private Bundle arguments;
    private final int[] pixels = new int[SIDE * SIDE];
    private final FloatBuffer tensor = FloatBuffer.allocate(3 * SIDE * SIDE);

    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        arguments = args;
        start();
    }

    @Override public void onStart() {
        Bundle output = new Bundle();
        int code = Activity.RESULT_CANCELED;
        try {
            output.putString("stream", "\nMECHAVISION_RESULT " + run().toString() + "\n");
            code = Activity.RESULT_OK;
        } catch (Exception error) {
            output.putString("stream", "\nMECHAVISION_ERROR " + error + "\n");
        }
        finish(code, output);
    }

    private JSONObject run() throws Exception {
        int iterations = parameter("iterations", 30, 5, 200);
        int warmup = parameter("warmup", 5, 1, 30);
        int threads = parameter("threads", 1, 1, 8);
        File folder = getTargetContext().getFilesDir();
        File model = new File(folder, "sa24.onnx");
        verify(model);
        int idlePss = pss();
        Bitmap source = BitmapFactory.decodeFile(new File(folder, "frame.png").getPath());
        if (source == null) throw new IllegalArgumentException("Missing or invalid upright frame.png");
        final int width = source.getWidth();
        final int height = source.getHeight();
        double[] stages = new double[iterations];
        double[] runtime = new double[iterations];
        JSONObject result = new JSONObject();
        OrtEnvironment env = OrtEnvironment.getEnvironment();
        try (OrtSession.SessionOptions options = new OrtSession.SessionOptions()) {
            options.setIntraOpNumThreads(threads);
            options.setInterOpNumThreads(1);
            long loadStart = SystemClock.elapsedRealtimeNanos();
            try (OrtSession session = env.createSession(model.getPath(), options)) {
                result.put("model_session_load_ms", elapsed(loadStart, SystemClock.elapsedRealtimeNanos()));
                int loaded = pss();
                for (int i = 0; i < warmup; i++) infer(source, env, session);
                int warmPss = pss();
                for (int i = 0; i < iterations; i++) {
                    double[] timings = infer(source, env, session);
                    stages[i] = timings[0];
                    runtime[i] = timings[1];
                }
                int sampledPeak = warmPss;
                for (int i = 0; i < 5; i++) {
                    infer(source, env, session);
                    sampledPeak = Math.max(sampledPeak, pss());
                }
                result.put("pss_kib", new JSONObject()
                    .put("before_decode_and_session", idlePss)
                    .put("after_decode_and_session", loaded)
                    .put("after_warmup", warmPss)
                    .put("max_sampled_after_frame", Math.max(loaded, sampledPeak)));
            }
        } finally {
            source.recycle();
        }
        return result.put("manufacturer", Build.MANUFACTURER)
            .put("device", Build.MODEL).put("android_api", Build.VERSION.SDK_INT)
            .put("abis", new JSONArray(Arrays.asList(Build.SUPPORTED_ABIS)))
            .put("runtime", "ONNX Runtime Android 1.22.0 CPU")
            .put("model_bytes", model.length()).put("model_sha256", SHA256)
            .put("source_width_px", width).put("source_height_px", height)
            .put("threads", threads).put("iterations", iterations).put("warmup", warmup)
            .put("resize_tensor_forward_copy_ms", distribution(stages))
            .put("ort_forward_only_ms", distribution(runtime));
    }

    private double[] infer(Bitmap source, OrtEnvironment env, OrtSession session) throws Exception {
        long start = SystemClock.elapsedRealtimeNanos();
        float scale = Math.min(1f, INPUT_CAP / (float) Math.max(source.getWidth(), source.getHeight()));
        Bitmap capped = Bitmap.createScaledBitmap(source, Math.max(1, Math.round(source.getWidth()*scale)),
                Math.max(1, Math.round(source.getHeight()*scale)), true);
        Bitmap scaled = Bitmap.createScaledBitmap(capped, SIDE, SIDE, true);
        try {
            scaled.getPixels(pixels, 0, SIDE, 0, 0, SIDE, SIDE);
            tensor.clear();
            for (int shift = 16; shift >= 0; shift -= 8) {
                for (int rgb : pixels) tensor.put(((rgb >> shift) & 255) / 255f);
            }
            tensor.flip();
            try (OnnxTensor input = OnnxTensor.createTensor(env, tensor, new long[]{1, 3, SIDE, SIDE})) {
                long forward = SystemClock.elapsedRealtimeNanos();
                try (OrtSession.Result prediction = session.run(Collections.singletonMap("img", input))) {
                    long ready = SystemClock.elapsedRealtimeNanos();
                    Object heatmap = prediction.get("heatmap").orElseThrow(() -> new IllegalStateException("Missing heatmap")).getValue();
                    if (!(heatmap instanceof float[][][][])
                            || ((float[][][][]) heatmap).length != 1
                            || ((float[][][][]) heatmap)[0].length != 4) {
                        throw new IllegalStateException("Expected four heatmap channels");
                    }
                    return new double[]{elapsed(start, SystemClock.elapsedRealtimeNanos()), elapsed(forward, ready)};
                }
            }
        } finally {
            if (scaled != capped) scaled.recycle();
            if (capped != source) capped.recycle();
        }
    }

    private int parameter(String name, int fallback, int min, int max) {
        int number = Integer.parseInt(arguments.getString(name, Integer.toString(fallback)));
        if (number < min || number > max) throw new IllegalArgumentException("Invalid " + name);
        return number;
    }

    private static void verify(File model) throws Exception {
        if (!model.isFile() || model.length() != MODEL_BYTES) {
            throw new IllegalArgumentException("Expected the pinned 83,084,930 byte SA24 model");
        }
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] buffer = new byte[65536];
        try (FileInputStream stream = new FileInputStream(model)) {
            for (int n; (n = stream.read(buffer)) != -1;) digest.update(buffer, 0, n);
        }
        StringBuilder hex = new StringBuilder();
        for (byte value : digest.digest()) hex.append(String.format(java.util.Locale.ROOT, "%02x", value & 255));
        if (!SHA256.contentEquals(hex)) throw new IllegalArgumentException("SA24 checksum mismatch");
    }

    private static int pss() {
        Debug.MemoryInfo info = new Debug.MemoryInfo();
        Debug.getMemoryInfo(info);
        return info.getTotalPss();
    }

    private static double elapsed(long start, long end) {
        return (end - start) / 1_000_000.0;
    }

    private static JSONObject distribution(double[] samples) throws Exception {
        double[] ordered = samples.clone();
        Arrays.sort(ordered);
        return new JSONObject().put("samples", new JSONArray(samples))
            .put("median", percentile(ordered, .5)).put("p95", percentile(ordered, .95));
    }

    private static double percentile(double[] sorted, double fraction) {
        double index = fraction * (sorted.length - 1);
        int lower = (int) index;
        return sorted[lower] + (index - lower) * (sorted[(int) Math.ceil(index)] - sorted[lower]);
    }
}
