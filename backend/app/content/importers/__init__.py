"""One module per supported import format. Each exposes a `to_prosemirror`
function that turns raw bytes into a whitelisted ProseMirror document (see
`app.content.sanitize`), matching the conversion table in PRD §4.3.
"""
