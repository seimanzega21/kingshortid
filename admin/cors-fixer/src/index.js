export default {
    async fetch(request, env, ctx) {
        // 1. Fetch original content
        const response = await fetch(request);

        // 2. Clone response to makes it mutable
        const newResponse = new Response(response.body, response);

        // 3. Force CORS Headers (Wildcard)
        newResponse.headers.set("Access-Control-Allow-Origin", "*");
        newResponse.headers.set("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS");
        newResponse.headers.set("Access-Control-Allow-Headers", "*");

        // 4. Return modified response
        return newResponse;
    },
};
