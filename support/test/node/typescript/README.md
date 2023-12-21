# Howto

This example shows you how to use vimspector with
[vscode-js-debug](https://github.com/microsoft/vscode-js-debug). For all
available options see
[here](https://github.com/microsoft/vscode-js-debug/blob/main/OPTIONS.md#node-attach).

## Prerequisites

- Have nodejs installed (was tested with 18 and 20 but should work with any).
- Ensure you have vscode-js-debug installed, check installation guides for
  nodejs of the vimspector repo on how to do so.
- Install dependencies `npm i`.

## Debugging

- Build the project `npm run build`
- Open the typescript file with vim `vim ./src/index.ts`
- Set breakpoints at line 2 and 3 (standard key mapping is F9)
- Run debugging (standard key mapping is F5)
- Press F5 once again (you should see console log output)
- Press F5 once again (you should see another console log output)
- Done🎉
