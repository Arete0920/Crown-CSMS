import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/login", "/admin", "/teacher", "/parent", "/student"];

function toLinearChannel(channel) {
  const normalized = channel / 255;
  return normalized <= 0.03928
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

function getContrastRatio(foreground, background) {
  const foregroundLuminance = 0.2126 * toLinearChannel(foreground.r)
    + 0.7152 * toLinearChannel(foreground.g)
    + 0.0722 * toLinearChannel(foreground.b);
  const backgroundLuminance = 0.2126 * toLinearChannel(background.r)
    + 0.7152 * toLinearChannel(background.g)
    + 0.0722 * toLinearChannel(background.b);
  const lighter = Math.max(foregroundLuminance, backgroundLuminance);
  const darker = Math.min(foregroundLuminance, backgroundLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

async function getRenderedContrast(page, selector) {
  return page.locator(selector).first().evaluate((element) => {
    function parseRgb(colorValue) {
      const match = colorValue.match(/rgba?\(([^)]+)\)/i);
      if (!match) {
        return null;
      }

      const segments = match[1].split(",").map((segment) => segment.trim());
      return {
        r: Number(segments[0]),
        g: Number(segments[1]),
        b: Number(segments[2]),
        a: segments[3] === undefined ? 1 : Number(segments[3]),
      };
    }

    function blend(topColor, bottomColor) {
      const alpha = topColor.a;
      return {
        r: Math.round((topColor.r * alpha) + (bottomColor.r * (1 - alpha))),
        g: Math.round((topColor.g * alpha) + (bottomColor.g * (1 - alpha))),
        b: Math.round((topColor.b * alpha) + (bottomColor.b * (1 - alpha))),
        a: 1,
      };
    }

    function resolveBackground(node) {
      let current = node;
      let background = { r: 255, g: 255, b: 255, a: 1 };

      while (current) {
        const parsed = parseRgb(getComputedStyle(current).backgroundColor);
        if (parsed && parsed.a > 0) {
          background = parsed.a >= 1 ? parsed : blend(parsed, background);
          if (parsed.a >= 1) {
            break;
          }
        }
        current = current.parentElement;
      }

      return background;
    }

    function toLinearChannelValue(channel) {
      const normalized = channel / 255;
      return normalized <= 0.03928
        ? normalized / 12.92
        : ((normalized + 0.055) / 1.055) ** 2.4;
    }

    function getContrastRatioValue(foreground, background) {
      const foregroundLuminance = 0.2126 * toLinearChannelValue(foreground.r)
        + 0.7152 * toLinearChannelValue(foreground.g)
        + 0.0722 * toLinearChannelValue(foreground.b);
      const backgroundLuminance = 0.2126 * toLinearChannelValue(background.r)
        + 0.7152 * toLinearChannelValue(background.g)
        + 0.0722 * toLinearChannelValue(background.b);
      const lighter = Math.max(foregroundLuminance, backgroundLuminance);
      const darker = Math.min(foregroundLuminance, backgroundLuminance);
      return (lighter + 0.05) / (darker + 0.05);
    }

    const styles = getComputedStyle(element);
    const foreground = parseRgb(styles.webkitTextFillColor) || parseRgb(styles.color) || { r: 0, g: 0, b: 0, a: 1 };
    const background = resolveBackground(element);

    return {
      color: styles.color,
      webkitTextFillColor: styles.webkitTextFillColor,
      backgroundColor: styles.backgroundColor,
      contrastRatio: getContrastRatioValue(foreground, background),
    };
  });
}

async function getBlockingViolations(page, violations) {
  const blockingViolations = [];

  for (const violation of violations) {
    if (violation.id !== "color-contrast") {
      blockingViolations.push(violation);
      continue;
    }

    const failingNodes = [];
    for (const node of violation.nodes) {
      const selector = node.target?.[0];
      if (!selector) {
        failingNodes.push(node);
        continue;
      }

      if (await page.locator(selector).count() === 0) {
        failingNodes.push(node);
        continue;
      }

      const renderedContrast = await getRenderedContrast(page, selector);
      if (renderedContrast.contrastRatio < 4.5) {
        failingNodes.push({ ...node, renderedContrast });
      }
    }

    if (failingNodes.length > 0) {
      blockingViolations.push({ ...violation, nodes: failingNodes });
    }
  }

  return blockingViolations;
}

for (const route of routes) {
  test(`a11y smoke ${route}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const candidateViolations = results.violations.filter((violation) => ["critical", "serious"].includes(violation.impact || ""));
    const blockingViolations = await getBlockingViolations(page, candidateViolations);

    if (blockingViolations.length > 0) {
      console.warn(`[a11y][blocking] ${route}: ${blockingViolations.length} blocking violations`);
      for (const violation of blockingViolations) {
        const targets = violation.nodes.flatMap((node) => node.target || []).join(", ");
        console.warn(`[a11y][blocking] ${route} :: ${violation.id} :: ${targets}`);
        for (const node of violation.nodes) {
          if (node.failureSummary) {
            const renderedSuffix = node.renderedContrast
              ? ` :: rendered=${node.renderedContrast.contrastRatio.toFixed(2)} ${node.renderedContrast.color} on ${node.renderedContrast.backgroundColor}`
              : "";
            console.warn(`[a11y][blocking-detail] ${route} :: ${violation.id} :: ${(node.target || []).join(" | ")} :: ${node.failureSummary.replaceAll(/\s+/g, " ").trim()}${renderedSuffix}`);
          }
        }
      }
    }

    expect(blockingViolations, `Accessibility violations on ${route}`).toEqual([]);
  });
}
