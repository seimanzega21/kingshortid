const fetch = require('node-fetch');

async function run() {
    const loginUrl = 'http://localhost:3000/api/admin/auth/login';
    const categoriesUrl = 'http://localhost:3000/api/categories';

    console.log("Trying to login to", loginUrl);
    
    // We try admin@kingshort.app first
    let email = 'admin@kingshort.app';
    let password = 'admin123';
    
    let res = await fetch(loginUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    
    let data = await res.json();
    console.log("Login with admin@kingshort.app response status:", res.status);
    
    if (!res.ok) {
        console.log("Failed with admin@kingshort.app. Trying admin@kingshort.com...");
        email = 'admin@kingshort.com';
        res = await fetch(loginUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        data = await res.json();
        console.log("Login with admin@kingshort.com response status:", res.status);
    }
    
    if (!res.ok) {
        console.error("Login failed:", data);
        return;
    }
    
    console.log("Login successful! Token:", data.token ? data.token.substring(0, 30) + '...' : 'none');
    
    // Get cookies
    const cookieHeader = res.headers.get('set-cookie');
    console.log("Set-Cookie header:", cookieHeader);
    
    if (!cookieHeader) {
        console.error("No cookie returned!");
        return;
    }
    
    // Extract admin_token cookie
    const adminTokenCookie = cookieHeader.split(';')[0];
    console.log("Extracted Cookie:", adminTokenCookie);
    
    console.log("Fetching categories with cookie...");
    const catRes = await fetch(categoriesUrl, {
        headers: { 'Cookie': adminTokenCookie }
    });
    
    const catData = await catRes.json();
    console.log("Categories response status:", catRes.status);
    console.log("Categories response body:", catData);
}

run().catch(console.error);
