export type CrownStatus = "pass" | "review" | "fail";

export function crownStatusFromBoolean(value: boolean | null | undefined): CrownStatus {
  if (value === true) return "pass";
  if (value === false) return "fail";
  return "review";
}

export function crownFormatCount(value: number | null | undefined): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "0";
  return new Intl.NumberFormat("en-US").format(value);
}

export function crownClassName(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
