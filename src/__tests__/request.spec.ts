/**
 * Unit tests for requestAPI: the message of the error that an answer of the
 * server raises when it is not a 2xx answer.
 */

import { ServerConnection } from '@jupyterlab/services';

import { requestAPI } from '../request';

const SETTINGS = { baseUrl: 'http://lab.test/' } as ServerConnection.ISettings;

/** Make the next request answer with this status and this body text. */
function answer(status: number, body: string): void {
  const response = {
    ok: status >= 200 && status < 300,
    status,
    text: async () => body
  } as unknown as Response;
  jest.spyOn(ServerConnection, 'makeRequest').mockResolvedValue(response);
}

describe('requestAPI', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('returns the parsed body of a 2xx answer', async () => {
    answer(200, '{"terminal_name": "3"}');

    await expect(requestAPI('launch-terminal', SETTINGS)).resolves.toEqual({
      terminal_name: '3'
    });
  });

  it('gives the code of a refusal as the message of the error, not the body object', async () => {
    answer(400, '{"error": "invalid_cwd"}');

    const refusal = requestAPI('launch-terminal', SETTINGS);

    await expect(refusal).rejects.toBeInstanceOf(
      ServerConnection.ResponseError
    );
    await expect(refusal).rejects.toThrow('invalid_cwd');
    await expect(refusal).rejects.not.toThrow('[object Object]');
  });

  it('prefers the field message of the body over the field error', async () => {
    answer(
      500,
      '{"message": "No terminal service", "error": "terminal_create_failed"}'
    );

    await expect(requestAPI('launch-terminal', SETTINGS)).rejects.toThrow(
      'No terminal service'
    );
  });

  it('gives a body that is no JSON as the message of the error', async () => {
    jest.spyOn(console, 'log').mockImplementation(() => undefined);
    answer(502, 'Bad Gateway');

    await expect(requestAPI('launch-terminal', SETTINGS)).rejects.toThrow(
      'Bad Gateway'
    );
  });
});
