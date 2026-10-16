#!/bin/bash
# Notas Workflow Mac - gera o app para Mac com Apple Silicon (M1, M2, M3, M4).
#
#   ./build-app.sh            compila e gera "build/Notas Workflow Mac.app"
#   ./build-app.sh --instalar também copia o app para a pasta Aplicativos
#
# Precisa só das Command Line Tools da Apple (xcode-select --install); o Xcode não é necessário.
# Antes de gerar o app, roda os autotestes (NotasSelfTest) e para se algum falhar.
set -euo pipefail
cd "$(dirname "$0")"

APP_NAME="Notas Workflow Mac"
APP="build/$APP_NAME.app"

echo "== Autotestes"
swift run -c release NotasSelfTest

echo "== Compilando para arm64"
swift build -c release --arch arm64 --product NotasWorkflowMac
BIN="$(swift build -c release --arch arm64 --product NotasWorkflowMac --show-bin-path)/NotasWorkflowMac"

echo "== Montando $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/NotasWorkflowMac"
cp Info.plist "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"
# Assinatura local (ad hoc): basta para usar o app no próprio Mac.
codesign --force --deep --sign - "$APP"

if [[ "${1:-}" == "--instalar" ]]; then
	echo "== Instalando em /Applications"
	osascript -e "tell application \"$APP_NAME\" to quit" >/dev/null 2>&1 || true
	rm -rf "/Applications/$APP_NAME.app"
	cp -R "$APP" "/Applications/"
	echo "Instalado em /Applications/$APP_NAME.app"
else
	echo "Pronto: $APP"
fi
