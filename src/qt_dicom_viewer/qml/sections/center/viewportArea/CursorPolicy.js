.pragma library

// Match interaction dispatch: region handles first, then crosshair handles,
// then the current tool. A drag latches this result until mouse release.
function resolve(interaction, region, crosshair, measurement) {
    if (interaction === "mpr:voi" || interaction === "mpr:segmentation")
        return region || interaction.slice(4)
    if (interaction === "annotate:text") return "annotate-text"
    if (crosshair === "center") return "crosshair-move"
    if (crosshair === "horizontalLine" || crosshair === "verticalLine")
        return "crosshair-rotate"
    const drawing = {"measure:length":"measure-line", "measure:angle":"measure-angle",
        "measure:rect":"measure-rect", "measure:ellipse":"measure-ellipse",
        "annotate:arrow":"annotate-arrow", "service:mtf":"mtf", "service:qa":"qa"}
    if (drawing[interaction]) return measurement || drawing[interaction]
    return ({window:"window", scroll:"scroll", pan:"pan", zoom:"zoom",
        "mpr:rotate3d":"rotate-3d", "volume:rotate":"rotate-3d", "volume:crop":"volume-crop"})[interaction] || ""
}
