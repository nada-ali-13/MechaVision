using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace MechaVision.UI
{
    public static class ArabicText
    {
        private enum Direction { Neutral, Left, Right }

        private struct Glyph
        {
            public char Base;
            public string Marks;
            public string Forms;
            public Direction Direction;
        }

        public static string ToVisualLine(string text)
        {
            if (string.IsNullOrEmpty(text))
                return string.Empty;

            var glyphs = new List<Glyph>(text.Length);
            bool hasArabic = false;
            foreach (char character in text)
            {
                if (char.GetUnicodeCategory(character) == UnicodeCategory.NonSpacingMark && glyphs.Count > 0)
                {
                    Glyph previous = glyphs[glyphs.Count - 1];
                    previous.Marks += character;
                    glyphs[glyphs.Count - 1] = previous;
                    continue;
                }

                Direction direction = DirectionOf(character);
                hasArabic |= direction == Direction.Right;
                ArabicForms.Glyphs.TryGetValue(character, out string forms);
                glyphs.Add(new Glyph { Base = character, Forms = forms, Direction = direction });
            }
            if (!hasArabic)
                return text;

            CombineLamAlef(glyphs);
            ShapeJoiningLetters(glyphs);
            ResolveNeutrals(glyphs);

            var visual = new StringBuilder(text.Length);
            for (int end = glyphs.Count - 1; end >= 0;)
            {
                Direction direction = glyphs[end].Direction;
                int start = end;
                while (start > 0 && glyphs[start - 1].Direction == direction)
                    --start;

                if (direction == Direction.Right)
                {
                    for (int index = end; index >= start; --index)
                        visual.Append(Mirror(glyphs[index].Base)).Append(glyphs[index].Marks);
                }
                else
                {
                    for (int index = start; index <= end; ++index)
                        visual.Append(glyphs[index].Base).Append(glyphs[index].Marks);
                }
                end = start - 1;
            }
            return visual.ToString();
        }

        private static Direction DirectionOf(char character)
        {
            if (char.IsDigit(character))
                return Direction.Left;
            if (character >= '\u0600' && character <= '\u08ff' ||
                character >= '\ufb50' && character <= '\ufefc')
            {
                return char.IsLetter(character) || character == '\u0640' ? Direction.Right : Direction.Neutral;
            }
            return char.IsLetter(character) ? Direction.Left : Direction.Neutral;
        }

        private static void CombineLamAlef(List<Glyph> glyphs)
        {
            for (int index = 0; index + 1 < glyphs.Count; ++index)
            {
                Glyph lam = glyphs[index];
                if (lam.Base != '\u0644')
                    continue;

                Glyph alef = glyphs[index + 1];
                switch (alef.Base)
                {
                    case '\u0622': lam.Forms = "\ufef5\ufef6\0\0"; break;
                    case '\u0623': lam.Forms = "\ufef7\ufef8\0\0"; break;
                    case '\u0625': lam.Forms = "\ufef9\ufefa\0\0"; break;
                    case '\u0627': lam.Forms = "\ufefb\ufefc\0\0"; break;
                    default: continue;
                }
                lam.Marks += alef.Marks;
                glyphs[index] = lam;
                glyphs.RemoveAt(index + 1);
            }
        }

        private static void ShapeJoiningLetters(List<Glyph> glyphs)
        {
            for (int index = 0; index < glyphs.Count; ++index)
            {
                Glyph glyph = glyphs[index];
                if (glyph.Forms == null)
                    continue;

                bool before = index > 0 && CanJoinNext(glyphs[index - 1]) && CanJoinPrevious(glyph);
                bool after = index + 1 < glyphs.Count && CanJoinNext(glyph) && CanJoinPrevious(glyphs[index + 1]);
                char form = glyph.Forms[before ? after ? 3 : 1 : after ? 2 : 0];
                if (form != '\0')
                {
                    glyph.Base = form;
                    glyphs[index] = glyph;
                }
            }
        }

        private static bool CanJoinNext(Glyph glyph)
        {
            return glyph.Base == '\u0640' || (glyph.Forms != null && glyph.Forms[2] != '\0');
        }

        private static bool CanJoinPrevious(Glyph glyph)
        {
            return glyph.Base == '\u0640' || (glyph.Forms != null && glyph.Forms[1] != '\0');
        }

        private static void ResolveNeutrals(List<Glyph> glyphs)
        {
            Direction previous = Direction.Right;
            for (int start = 0; start < glyphs.Count;)
            {
                if (glyphs[start].Direction != Direction.Neutral)
                {
                    previous = glyphs[start++].Direction;
                    continue;
                }

                int end = start;
                while (end < glyphs.Count && glyphs[end].Direction == Direction.Neutral)
                    ++end;
                Direction next = end < glyphs.Count ? glyphs[end].Direction : Direction.Right;
                for (int index = start; index < end; ++index)
                {
                    Glyph glyph = glyphs[index];
                    glyph.Direction = previous == next ? previous : Direction.Right;
                    glyphs[index] = glyph;
                }
                start = end;
            }
        }

        private static char Mirror(char character)
        {
            switch (character)
            {
                case '(': return ')';
                case ')': return '(';
                case '[': return ']';
                case ']': return '[';
                case '{': return '}';
                case '}': return '{';
                case '<': return '>';
                case '>': return '<';
                case '«': return '»';
                case '»': return '«';
                default: return character;
            }
        }
    }
}
