import { test } from "~~/test/playwright/utils/test"
import breakpoints, {
  isMobileBreakpoint,
} from "~~/test/playwright/utils/breakpoints"
import { hideInputCursors } from "~~/test/playwright/utils/page"
import {
  filters,
  goToSearchTerm,
  preparePageForTests,
  scrollToBottom,
  sleep,
} from "~~/test/playwright/utils/navigation"
import { languageDirections } from "~~/test/playwright/utils/i18n"

test.describe.configure({ mode: "parallel" })

const headerSelector = ".main-header"

for (const dir of languageDirections) {
  test.describe(dir, () => {
    breakpoints.describeEvery(({ breakpoint, expectSnapshot }) => {
      test.beforeEach(async ({ page }) => {
        await preparePageForTests(page, breakpoint, { dismissFilter: false })

        await goToSearchTerm(page, "birds", { dir })
      })

      test("filters open", async ({ page }) => {
        await page.mouse.move(0, 150)
        await expectSnapshot(
          page,
          "filters-open",
          page.locator(headerSelector),
          { dir }
        )
      })

      test.describe("starting with closed filters", () => {
        test.beforeEach(async ({ page }) => {
          // By default, filters are open on desktop. We need to close them.
          if (!isMobileBreakpoint(breakpoint)) {
            await filters.close(page)
          }
        })

        test("resting", async ({ page }) => {
          // Make sure the header is not hovered on
          await page.mouse.move(0, 150)
          await expectSnapshot(page, "resting", page.locator(headerSelector), {
            dir,
          })
        })

        test("scrolled", async ({ page }) => {
          await scrollToBottom(page)
          await page.mouse.move(0, 150)
          await sleep(200)
          await expectSnapshot(page, "scrolled", page.locator(headerSelector), {
            dir,
          })
        })

        test("searchbar hovered", async ({ page }) => {
          await page.hover("input")
          await hideInputCursors(page)
          await expectSnapshot(
            page,
            "searchbar-hovered",
            page.locator(headerSelector),
            { dir }
          )
        })

        test("searchbar active", async ({ page }) => {
          await hideInputCursors(page)
          await page.click("input")
          // Search takes up the entire view on mobile
          // But on desktop, to reduce the snapshot size, we can scope the
          // locator just to the header
          // eslint-disable-next-line playwright/no-conditional-in-test
          const locator = isMobileBreakpoint(breakpoint)
            ? page
            : page.locator(headerSelector)
          await expectSnapshot(page, "searchbar-active", locator, { dir })
        })
      })
    })
  })
}
