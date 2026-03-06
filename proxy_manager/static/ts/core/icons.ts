/**
 * Icons Library
 * =============
 *
 * Generates `<svg><use href="#i-name"/>` references to the
 * SVG sprite embedded in admin.html (icons-sprite.html).
 */

/** Returns an inline SVG element referencing a sprite symbol. */
export function icon(name: string, size: number = 14, sw: number = 2, cls: string = ""): string {
    return `<svg width="${size}" height="${size}" stroke-width="${sw}"${cls ? ` class="${cls}"` : ""}><use href="#i-${name}"/></svg>`;
}

export const SVG = {
    edit: icon("edit-document"),
    editSm: icon("edit-document", 12),
    del: icon("trash"),
    delSm: icon("trash", 12),
    plus: icon("plus"),
    chevron: icon("chevron-down", 14, 2, "chevron"),
    arrow: `<svg width="24" height="24" stroke-width="1.5" opacity=".4"><use href="#i-arrow-right-narrow"/></svg>`,
    lock: icon("lock"),
    code: icon("code"),
    copy: icon("copy"),
} as const;
