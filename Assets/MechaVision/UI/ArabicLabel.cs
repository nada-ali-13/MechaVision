using System;
using System.Text;
using UnityEngine;
using UnityEngine.UI;

namespace MechaVision.UI
{
    [AddComponentMenu("")]
    public sealed class ArabicLabel : Text
    {
        private string logicalText = string.Empty;
        private bool wrap;
        private float lastWidth = -1f;
        private TextGenerator measure;

        public void SetContent(string content, bool wrapWords = true)
        {
            content = content ?? string.Empty;
            if (logicalText == content && wrap == wrapWords)
                return;

            logicalText = content;
            wrap = wrapWords;
            Refresh();
        }

        protected override void OnRectTransformDimensionsChange()
        {
            base.OnRectTransformDimensionsChange();
            if (wrap && !Mathf.Approximately(lastWidth, rectTransform.rect.width))
                Refresh();
        }

        private void Refresh()
        {
            lastWidth = rectTransform.rect.width;
            var result = new StringBuilder(logicalText.Length);
            string[] lines = logicalText.Split('\n');
            for (int index = 0; index < lines.Length; ++index)
            {
                if (index > 0)
                    result.Append('\n');

                string line = lines[index];
                if (!wrap || lastWidth < 20 || font == null)
                {
                    result.Append(ArabicText.ToVisualLine(line));
                    continue;
                }

                measure ??= new TextGenerator();
                var settings = GetGenerationSettings(Vector2.zero);
                settings.horizontalOverflow = HorizontalWrapMode.Overflow;
                string current = string.Empty;
                foreach (string word in line.Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries))
                {
                    string candidate = current.Length == 0 ? word : current + " " + word;
                    string visual = ArabicText.ToVisualLine(candidate);
                    float width = measure.GetPreferredWidth(visual, settings) / pixelsPerUnit;
                    if (current.Length > 0 && width > lastWidth)
                    {
                        result.Append(ArabicText.ToVisualLine(current)).Append('\n');
                        current = word;
                    }
                    else
                    {
                        current = candidate;
                    }
                }
                result.Append(ArabicText.ToVisualLine(current));
            }
            base.text = result.ToString();
        }
    }
}
