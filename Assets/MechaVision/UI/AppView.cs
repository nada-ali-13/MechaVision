using UnityEngine;
using UnityEngine.UI;

namespace MechaVision.UI
{
    internal sealed class AppView
    {
        internal static readonly Color Background = new Color32(13, 23, 34, 255);
        internal static readonly Color Surface = new Color32(26, 41, 56, 255);
        internal static readonly Color SurfaceRaised = new Color32(42, 59, 75, 255);
        internal static readonly Color Ink = new Color32(242, 248, 250, 255);
        internal static readonly Color Secondary = new Color32(190, 209, 220, 255);
        internal static readonly Color Mint = new Color32(128, 234, 202, 255);
        internal static readonly Color Amber = new Color32(255, 212, 132, 255);

        private readonly Font font;
        private readonly Font mono;
        private readonly Sprite rounded;

        internal AppView(Font font, Font mono)
        {
            this.font = font;
            this.mono = mono;
            rounded = MakeRoundedSprite();
        }

        internal void Dispose()
        {
            Object.Destroy(rounded.texture);
            Object.Destroy(rounded);
        }

        internal static RectTransform Rect(Transform parent, string name)
        {
            var item = new GameObject(name, typeof(RectTransform));
            var rect = (RectTransform)item.transform;
            rect.SetParent(parent, false);
            return rect;
        }

        internal static void Fill(RectTransform rect, float margin = 0f)
        {
            Place(rect, Vector2.zero, Vector2.one, new Vector2(margin, margin), new Vector2(-margin, -margin));
        }

        internal static void Place(RectTransform rect, Vector2 min, Vector2 max, Vector2 offsetMin, Vector2 offsetMax)
        {
            rect.anchorMin = min;
            rect.anchorMax = max;
            rect.offsetMin = offsetMin;
            rect.offsetMax = offsetMax;
        }

        internal static void Clear(Transform parent)
        {
            while (parent.childCount > 0)
            {
                Transform child = parent.GetChild(parent.childCount - 1);
                child.gameObject.SetActive(false);
                child.SetParent(null);
                Object.Destroy(child.gameObject);
            }
        }

        internal RectTransform Stack(Transform parent, string name, float gap = 10f, int padding = 0)
        {
            RectTransform rect = Rect(parent, name);
            var layout = rect.gameObject.AddComponent<VerticalLayoutGroup>();
            layout.childAlignment = TextAnchor.UpperCenter;
            layout.spacing = gap;
            layout.padding = new RectOffset(padding, padding, padding, padding);
            layout.childControlHeight = true;
            layout.childControlWidth = true;
            layout.childForceExpandHeight = false;
            layout.childForceExpandWidth = true;
            return rect;
        }

        internal RectTransform Row(Transform parent, string name, float gap = 8f)
        {
            RectTransform rect = Rect(parent, name);
            var layout = rect.gameObject.AddComponent<HorizontalLayoutGroup>();
            layout.spacing = gap;
            layout.childAlignment = TextAnchor.MiddleCenter;
            layout.childControlHeight = true;
            layout.childControlWidth = true;
            layout.childForceExpandHeight = false;
            layout.childForceExpandWidth = true;
            layout.reverseArrangement = true;
            return rect;
        }

        internal static void Height(RectTransform rect, float height, float flex = 0f)
        {
            var layout = rect.gameObject.GetComponent<LayoutElement>() ?? rect.gameObject.AddComponent<LayoutElement>();
            layout.minHeight = height;
            layout.preferredHeight = height;
            layout.flexibleHeight = flex;
        }

        internal RectTransform Card(Transform parent, string name, Color? tint = null)
        {
            RectTransform container = Stack(parent, name, 7f, 14);
            Plate(container, tint ?? Surface);
            return container;
        }

        internal Image Plate(RectTransform rect, Color tint, bool blockRaycasts = false)
        {
            var image = rect.gameObject.AddComponent<Image>();
            image.sprite = rounded;
            image.type = Image.Type.Sliced;
            image.color = tint;
            image.raycastTarget = blockRaycasts;
            return image;
        }

        internal ArabicLabel Label(Transform parent, string value, int size = 22,
            Color? color = null, TextAnchor align = TextAnchor.MiddleRight, bool wrap = true)
        {
            RectTransform rect = Rect(parent, "Label");
            ArabicLabel text = rect.gameObject.AddComponent<ArabicLabel>();
            Style(text, font, size, color ?? Ink, align);
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            text.SetContent(value, wrap);
            return text;
        }

        internal Text Code(Transform parent, string value)
        {
            RectTransform rect = Rect(parent, "Sketch");
            Text text = rect.gameObject.AddComponent<Text>();
            Style(text, mono, 17, Ink, TextAnchor.UpperLeft);
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.text = value;
            return text;
        }

        internal Button Button(Transform parent, string caption, UnityEngine.Events.UnityAction action,
            bool accent = false, int size = 20, float height = 54)
        {
            RectTransform rect = Rect(parent, caption);
            Image image = Plate(rect, accent ? Mint : SurfaceRaised, true);
            Button button = rect.gameObject.AddComponent<Button>();
            button.targetGraphic = image;
            ColorBlock colors = button.colors;
            colors.pressedColor = new Color32(186, 199, 205, 255);
            colors.disabledColor = new Color32(122, 127, 131, 255);
            button.colors = colors;
            Height(rect, height);
            ArabicLabel label = Label(rect, caption, size, accent ? Background : Ink, TextAnchor.MiddleCenter);
            Fill(label.rectTransform, 8);
            button.onClick.AddListener(action);
            return button;
        }

        internal InputField Input(Transform parent, string value, string hint, bool numeric, float height = 54)
        {
            RectTransform rect = Rect(parent, numeric ? "Value" : "Search");
            Image image = Plate(rect, SurfaceRaised, true);
            InputField input = rect.gameObject.AddComponent<InputField>();
            input.targetGraphic = image;
            input.contentType = numeric ? InputField.ContentType.DecimalNumber : InputField.ContentType.Standard;
            input.characterLimit = numeric ? 12 : 100;
            input.caretColor = Mint;
            input.customCaretColor = true;
            input.selectionColor = new Color32(40, 110, 110, 160);
            Height(rect, height);
            Text text = Rect(rect, "Input text").gameObject.AddComponent<Text>();
            Style(text, font, 20, Ink, numeric ? TextAnchor.MiddleCenter : TextAnchor.MiddleRight);
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            Fill(text.rectTransform, 10);
            ArabicLabel placeholder = Label(rect, hint, 18, Secondary);
            Fill(placeholder.rectTransform, 10);
            input.textComponent = text;
            input.placeholder = placeholder;
            input.SetTextWithoutNotify(value);
            return input;
        }

        internal RectTransform Scroll(Transform parent, string name)
        {
            RectTransform rect = Rect(parent, name);
            Height(rect, 0, 1);
            ScrollRect scroll = rect.gameObject.AddComponent<ScrollRect>();

            RectTransform viewport = Rect(rect, "Viewport");
            Fill(viewport);
            var target = viewport.gameObject.AddComponent<Image>();
            target.color = Color.clear;
            viewport.gameObject.AddComponent<RectMask2D>();

            RectTransform content = Stack(viewport, "Content", 10f, 3);
            content.anchorMin = new Vector2(0f, 1f);
            content.anchorMax = new Vector2(1f, 1f);
            content.pivot = new Vector2(0.5f, 1f);
            content.anchoredPosition = Vector2.zero;
            content.sizeDelta = Vector2.zero;
            content.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;

            scroll.viewport = viewport;
            scroll.content = content;
            scroll.horizontal = false;
            scroll.movementType = ScrollRect.MovementType.Clamped;
            scroll.scrollSensitivity = 46f;
            return content;
        }

        private static void Style(Text label, Font chosenFont, int size, Color color, TextAnchor align)
        {
            label.font = chosenFont;
            label.fontSize = size;
            label.color = color;
            label.alignment = align;
            label.supportRichText = false;
            label.raycastTarget = false;
            label.verticalOverflow = VerticalWrapMode.Overflow;
        }

        private static Sprite MakeRoundedSprite()
        {
            const int size = 32;
            const int radius = 12;
            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false) { name = "Rounded panel" };
            var pixels = new Color32[size * size];
            for (int y = 0; y < size; ++y)
            {
                for (int x = 0; x < size; ++x)
                {
                    float dx = x - Mathf.Clamp(x, radius, size - radius - 1);
                    float dy = y - Mathf.Clamp(y, radius, size - radius - 1);
                    byte alpha = (byte)(255 * Mathf.Clamp01(radius + 0.5f - Mathf.Sqrt(dx * dx + dy * dy)));
                    pixels[y * size + x] = new Color32(255, 255, 255, alpha);
                }
            }
            texture.SetPixels32(pixels);
            texture.Apply(false, true);
            return Sprite.Create(texture, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100, 0,
                SpriteMeshType.FullRect, new Vector4(radius, radius, radius, radius));
        }
    }
}
