export class ApiError extends Error {
    public error: string;

    constructor(message:string, error:string){
        super(message);

        this.error = error;
    }
}

export async function callFetch<T>(
    route: string, token: string|null, 
    opts: RequestInit = {}
): Promise<T> {
    const headers = new Headers(opts.headers || {});

    headers.set("Content-Type", "application/json");

    if(token){
        headers.set("Authorization", `Bearer ${token}`);
    }

    const optsExt: RequestInit = {
        ...opts,
        headers: headers,
    };

    const response = await fetch(route, optsExt);

    if(response.ok){
        return response.json();
    } else {
        let textError: string = `Request failed: ${response.status}`;

        try{
            const raw = await response.text();
            const r: Record<string, unknown> = JSON.parse(raw);
            textError = (r.error as string) || (r.detail as string) || raw;
        } catch (err) {
            console.log(err);
        }
        const error = new ApiError (`Request failed: ${response.status}`, textError);
        throw error;
    }
};