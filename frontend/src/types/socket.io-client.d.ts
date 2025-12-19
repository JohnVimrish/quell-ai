declare module "socket.io-client" {
  export interface Socket {
    emit(event: string, ...args: any[]): Socket;
    on(event: string, callback: (...args: any[]) => void): Socket;
    disconnect(): void;
  }

  export interface SocketIOClientOptions {
    path?: string;
    transports?: string[];
    withCredentials?: boolean;
    auth?: Record<string, unknown>;
  }

  export function io(
    uri?: string,
    options?: SocketIOClientOptions,
  ): Socket;
}
