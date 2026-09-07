.pragma library

// Keep this order aligned with beginInteraction: region tools own the pointer;
// otherwise MPR crosshair targets precede annotation editing and view tools.
function resolve(interaction, region, crosshair, measurement) {
    if (interaction === "mpr:voi" || interaction === "mpr:segmentation")
        return region || interaction.slice(4)
    if (interaction === "annotate:text") return ""
    if (crosshair === "center") return "crosshair-move"
    if (crosshair === "horizontalLine" || crosshair === "verticalLine")
        return "crosshair-rotate"
    if (interaction.startsWith("measure:") || interaction.startsWith("annotate:")
            || interaction === "service:mtf" || interaction === "service:qa")
        return measurement || (interaction === "service:mtf" ? "mtf" : "")
    return ({ window: "window", scroll: "scroll", pan: "pan", zoom: "zoom",
              "mpr:rotate3d": "rotate-3d" })[interaction] || ""
}
