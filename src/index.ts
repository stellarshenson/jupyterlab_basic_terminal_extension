import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { requestAPI } from './request';

/**
 * Initialization data for the jupyterlab_basic_terminal_extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_basic_terminal_extension:plugin',
  description: 'Jupyterlab extension to make a command that allows launching a utility terminal that runs without shell. This can be used to start and show console utilities, that when finished - close the terminal window / tab',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension jupyterlab_basic_terminal_extension is activated!');

    requestAPI<any>('hello', app.serviceManager.serverSettings)
      .then(data => {
        console.log(data);
      })
      .catch(reason => {
        console.error(
          `The jupyterlab_basic_terminal_extension server extension appears to be missing.\n${reason}`
        );
      });
  }
};

export default plugin;
