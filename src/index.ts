import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './request';

export interface ILaunchTerminalArgs {
  argv: string[];
  cwd?: string;
}

export interface ILaunchTerminalResponse {
  terminal_name: string;
}

const COMMAND_LAUNCH = 'basic-terminal:launch';

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_basic_terminal_extension:plugin',
  description:
    'Launch a JupyterLab terminal whose pty runs a utility directly with no shell. The tab is focused on launch and closes when the process exits.',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    app.commands.addCommand(COMMAND_LAUNCH, {
      label: 'Launch utility terminal (shell-less)',
      caption:
        'Spawn a JupyterLab terminal whose only process is the supplied argv. Tab is focused on launch and closes when the process exits.',
      execute: async args => {
        const { argv, cwd } = (args as unknown) as ILaunchTerminalArgs;
        if (!Array.isArray(argv) || argv.length === 0) {
          throw new Error(
            `${COMMAND_LAUNCH}: argv must be a non-empty string array`
          );
        }
        const launched = await requestAPI<ILaunchTerminalResponse>(
          'launch-terminal',
          app.serviceManager.serverSettings,
          {
            method: 'POST',
            body: JSON.stringify({ argv, cwd })
          }
        );
        const widget: any = await app.commands.execute('terminal:open', {
          name: launched.terminal_name
        });
        if (widget?.id) {
          app.shell.activateById(widget.id);
        }
        const session = widget?.content?.session;
        if (session) {
          const disposeWidget = (): void => {
            if (widget && !widget.isDisposed) {
              widget.dispose();
            }
          };
          session.disposed?.connect?.(disposeWidget);
          session.connectionStatusChanged?.connect?.(
            (_: unknown, status: string) => {
              if (status === 'disconnected') {
                disposeWidget();
              }
            }
          );
        }
        return widget;
      }
    });
  }
};

export default plugin;
