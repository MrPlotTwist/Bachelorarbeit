export async function POST(req) {
  try {
    console.log("Next API: Request angekommen");

    const body = await req.json();
    console.log("Next API: Body =", body);

    const backendResponse = await fetch(process.env.CRAWLER_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    console.log("Next API: Backend Status =", backendResponse.status);

    const text = await backendResponse.text();
    console.log("Next API: Backend Body =", text);

    return new Response(text, {
      status: backendResponse.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Next API Fehler:", error);

    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}