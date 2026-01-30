import { readFileSync } from "fs";
import { join } from "path";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Read cached pools data
    const dataPath = join(process.cwd(), "data", "pools.json");
    const data = readFileSync(dataPath, "utf-8");
    const pools = JSON.parse(data);

    return NextResponse.json(pools);
  } catch (error: any) {
    if (error.code === "ENOENT") {
      return NextResponse.json(
        { error: "Data not available: pools.json missing" },
        { status: 503 }
      );
    }
    return NextResponse.json(
      { error: "Failed to read data: " + error.message },
      { status: 500 }
    );
  }
}
