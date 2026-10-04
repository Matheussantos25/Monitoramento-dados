import { retiredResponse } from "./retired.mjs";

// Keep the endpoint retired so already-installed APKs cannot incur API charges.
Deno.serve(retiredResponse);
