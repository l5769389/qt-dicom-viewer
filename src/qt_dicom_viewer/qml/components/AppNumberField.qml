import QtQuick
AppTextField {
    id: field
    required property real numberValue
    property real minimum: 0
    property real maximum: 100
    property int decimals: 2
    property bool publishing: false
    property bool commitOnFinish: false
    signal edited(real value)
    function sync() { text = String(Number(numberValue.toFixed(decimals))) }
    Component.onCompleted: sync()
    onNumberValueChanged: if (!publishing) sync()
    validator: DoubleValidator { locale: "C"; bottom: field.minimum; top: field.maximum; decimals: field.decimals; notation: DoubleValidator.StandardNotation }
    function publishNumber() {
        if (acceptableInput && text.trim() && Number.isFinite(Number(text))) {
            publishing = true
            edited(Number(text))
            publishing = false
        }
    }
    function commit() {
        if (commitOnFinish) publishNumber()
        sync()
    }
    onTextEdited: if (!commitOnFinish) publishNumber()
    onEditingFinished: commit()
    onActiveFocusChanged: if (!activeFocus) commit()
    Keys.onEscapePressed: sync()
}
