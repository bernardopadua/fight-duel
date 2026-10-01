interface Logger {
    error(message: string, data?: any): void;
    warn(message: string, data?: any): void;
}

const logger: Logger = {
    error(message: string, data?: any) {
        console.error(`ERROR: ${message}`, data);
    },
    warn(message: string, data?: any) {
        console.warn(`WARNING: ${message}`, data);
    }
}

export default logger;