const BASE_URL = process.env.NEXT_PUBLIC_API_BASE;

export async function checkUserStatus() {
  try {
    const response = await fetch(`${BASE_URL}/registration/user-status`);

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    const data = await response.json();
    return data.user_exists;
  } catch (error) {
    console.error("Error checking user status:", error);
    // In case of network error or API failure, return false
    return false;
  }
}

export async function sendChatMessage(message, personality = "friendly") {
  try {
    const response = await fetch(`${BASE_URL}/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        personality: personality,
      }),
    });

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error sending chat message:", error);
    throw error;
  }
}

// ฟังก์ชันดึงประวัติการแชท (ถ้าต้องการใช้ในอนาคต)
export async function getChatHistory(limit = 10) {
  try {
    const response = await fetch(`${BASE_URL}/chat/history?limit=${limit}`);

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching chat history:", error);
    return [];
  }
}

// ฟังก์ชันดึงข้อมูลผู้ใช้
export async function getUserInfo() {
  try {
    const response = await fetch(`${BASE_URL}/registration/user-info`);
    const text = await response.text();

    console.log("🧪 Raw response from /user-info:", text);
    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`);
    }

    return JSON.parse(text);
  } catch (error) {
    console.error("Error fetching user info:", error);
    return null;
  }
}
