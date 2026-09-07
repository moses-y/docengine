/** TipTap extension set trimmed to exactly what the server whitelists in
 * `app.content.sanitize` (PRD §4.2): StarterKit minus the nodes/marks we
 * don't support (code blocks, blockquotes, strike, links, images...), plus
 * Underline, which StarterKit doesn't include by default.
 */
import Underline from "@tiptap/extension-underline";
import StarterKit from "@tiptap/starter-kit";

export const editorExtensions = [
  StarterKit.configure({
    codeBlock: false,
    blockquote: false,
    horizontalRule: false,
    strike: false,
    code: false,
    heading: { levels: [1, 2, 3] },
  }),
  Underline,
];
