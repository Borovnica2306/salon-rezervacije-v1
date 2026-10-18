import asyncio
from playwright.async_api import async_playwright

BASE = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0]
OUT = "/app/frontend/public/mockups"
PAGES = {"settings": "/settings", "services": "/services", "workers": "/employees", "calendar": ""}

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        page = await ctx.new_page()
        await page.goto(f"{BASE}/beauty-studio-bor/admin/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "admin@salon.com")
        await page.fill('input[type="password"]', "Admin123!")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(4000)
        for name, path in PAGES.items():
            try:
                await page.goto(f"{BASE}/beauty-studio-bor/admin{path}", wait_until="domcontentloaded")
            except Exception:
                await page.wait_for_timeout(1000)
                await page.goto(f"{BASE}/beauty-studio-bor/admin{path}", wait_until="domcontentloaded")
            await page.wait_for_timeout(3500)
            if name == "services":
                btn = page.locator('[data-testid="expand-all-categories-btn"]')
                if await btn.count():
                    await btn.click()
                    await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUT}/{name}-mobile.png")
            print(name, "ok")
        await b.close()

asyncio.run(main())
