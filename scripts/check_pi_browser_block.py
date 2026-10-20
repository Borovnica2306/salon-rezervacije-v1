import asyncio
from playwright.async_api import async_playwright
async def run(p, ua, name, url):
    b=await p.chromium.launch(); ctx=await b.new_context(viewport={"width":390,"height":844}, user_agent=ua); page=await ctx.new_page()
    async def h(route):
        if route.request.method=="OPTIONS":
            return await route.fulfill(status=204, headers={"access-control-allow-origin":"http://127.0.0.2:3000","access-control-allow-credentials":"true","access-control-allow-headers":"*","access-control-allow-methods":"*"})
        r=await route.fetch(); hd=dict(r.headers); hd["access-control-allow-origin"]="http://127.0.0.2:3000"; hd["access-control-allow-credentials"]="true"
        await route.fulfill(response=r, headers=hd)
    await page.route("**/api/**", h)
    await page.goto(url, wait_until="domcontentloaded"); await page.wait_for_timeout(6000)
    print(name, "blocked:", await page.locator('[data-testid=pi-browser-required]').count(), "| Pi obj:", await page.evaluate("()=>typeof window.Pi"), "| text:", (await page.inner_text("body"))[:90].replace("\n"," "))
    await page.screenshot(path=f"/tmp/{name}.png"); await b.close()
async def main():
    async with async_playwright() as p:
        await run(p, "Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile", "normal", "http://127.0.0.2:3000/beauty-studio-bor")
        await run(p, "Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile PiBrowser/2.9", "pibrowser", "http://127.0.0.2:3000/beauty-studio-bor")
        await run(p, "Mozilla/5.0 (Linux; Android 13) Chrome/120 Mobile", "preview", open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0]+"/beauty-studio-bor")
asyncio.run(main())
