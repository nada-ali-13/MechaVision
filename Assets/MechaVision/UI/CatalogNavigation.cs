using System;
using System.Globalization;
using System.Text;
using MechaVision.Catalog;

namespace MechaVision.UI
{
    public static class CatalogNavigation
    {
        public static bool Matches(ProjectData project, string query, string category = null, string level = null)
        {
            if (project == null ||
                (!string.IsNullOrEmpty(category) && project.category != category) ||
                (!string.IsNullOrEmpty(level) && project.level != level))
            {
                return false;
            }

            string searchable = Normalize(string.Join(" ", project.name_ar, project.name_en,
                project.description_ar, project.id, string.Join(" ", project.aliases ?? Array.Empty<string>())));
            foreach (string term in Normalize(query).Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries))
            {
                if (searchable.IndexOf(term, StringComparison.Ordinal) < 0)
                    return false;
            }
            return true;
        }

        public static int MoveStep(int step, int delta, int stepCount)
        {
            return (int)Math.Max(0L, Math.Min((long)step + delta, stepCount));
        }

        private static string Normalize(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return string.Empty;

            var normalized = new StringBuilder(value.Length);
            foreach (char character in value.Normalize(NormalizationForm.FormKD).ToLowerInvariant())
            {
                UnicodeCategory category = CharUnicodeInfo.GetUnicodeCategory(character);
                if (character == '\u0640' || category == UnicodeCategory.NonSpacingMark ||
                    category == UnicodeCategory.SpacingCombiningMark)
                {
                    continue;
                }

                switch (character)
                {
                    case '\u0649':
                    case '\u06cc':
                        normalized.Append('\u064a');
                        break;
                    case '\u0629':
                        normalized.Append('\u0647');
                        break;
                    default:
                        normalized.Append(char.IsLetterOrDigit(character) ? character : ' ');
                        break;
                }
            }
            return normalized.ToString();
        }
    }
}
