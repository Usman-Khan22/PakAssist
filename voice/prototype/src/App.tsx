import { useRef, useState } from "react";

declare global {
  interface Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
  }
}

function App() {
  const [status, setStatus] = useState("idle");
  const [transcript, setTranscript] = useState("");
  const [answer, setAnswer] = useState("");
  const [voiceAnswer, setVoiceAnswer] = useState("");

  const sessionId = useRef<string | null>(null);

  const createSession = async () => {
    const response = await fetch("http://127.0.0.1:8001/sessions", {
      method: "POST",
      headers: {
        accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Could not create session");
    }

    const data = await response.json();

    sessionId.current = data.session_id;

    console.log("Voice session created:", data.session_id);

    return data.session_id;
  };

  const makeVoiceFriendly = (text: string) => {
  const cleaned = text
    .replace(/#{1,6}\s*/g, "")
    .replace(/\*\*/g, "")
    .replace(/\*/g, "")
    .replace(/□/g, "")
    .trim();

  // Extract bullet points
  const bullets = cleaned
    .split("\n")
    .map((line) =>
      line
        .replace(/^\s*[-•]\s*/, "")
        .trim()
    )
    .filter(
      (line) =>
        line.length > 0 &&
        !line.toLowerCase().startsWith("required documents") &&
        !line.toLowerCase().startsWith("note:")
    );

  // If answer looks like a document/checklist response
  if (
    cleaned.toLowerCase().includes("required documents") &&
    bullets.length > 0
  ) {
    const usefulItems = bullets
      .slice(0, 5)
      .map((item) =>
        item
          .replace(/\.$/, "")
          .replace(/\([^)]{80,}\)/g, "")
          .trim()
      );

    if (usefulItems.length === 1) {
      return `You will need ${usefulItems[0]}.`;
    }

    const lastItem = usefulItems.pop();

    return (
      `For this, you will need ${usefulItems.join(", ")}, ` +
      `and ${lastItem}. Please confirm the final requirements for your province.`
    );
  }

  // Generic fallback for non-list answers
  const plainText = cleaned
    .replace(/\n+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const sentences =
    plainText.match(/[^.!?]+[.!?]+/g) || [];

  if (sentences.length > 0) {
    const summary = sentences
      .slice(0, 2)
      .join(" ")
      .trim();

    return summary;
  }

  return plainText.length > 350
    ? plainText.slice(0, 350) + "."
    : plainText;
};

  const speakAnswer = async (text: string) => {
    try {
      setStatus("speaking");

      const response = await fetch(
        "http://127.0.0.1:8001/voice/tts",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: text,
          }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();

        console.error("TTS backend error:", errorText);

        throw new Error("TTS request failed");
      }

      const audioBlob = await response.blob();

      const audioUrl = URL.createObjectURL(audioBlob);

      const audio = new Audio(audioUrl);

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
        setStatus("idle");
      };

      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        setStatus("error");
      };

      await audio.play();
    } catch (error) {
      console.error("TTS error:", error);
      setStatus("error");
    }
  };

  const askPakAssist = async (message: string) => {
    try {
      setStatus("thinking");
      setAnswer("");
      setVoiceAnswer("");

      let currentSessionId = sessionId.current;

      if (!currentSessionId) {
        currentSessionId = await createSession();
      }

      const response = await fetch("http://127.0.0.1:8001/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          accept: "application/json",
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          message: message,
        }),
      });

      if (!response.ok) {
        const errorBody = await response.text();

        console.error("Backend response:", errorBody);

        throw new Error(
          `Backend request failed: ${response.status}`
        );
      }

      const data = await response.json();

      setAnswer(data.response);

      const shortVoiceResponse =
        makeVoiceFriendly(data.response);

      setVoiceAnswer(shortVoiceResponse);

      await speakAnswer(shortVoiceResponse);
    } catch (error) {
      console.error(error);
      setStatus("error");
    }
  };

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setStatus("unsupported");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-PK";

    recognition.onstart = () => {
      setStatus("listening");
      setTranscript("");
      setAnswer("");
      setVoiceAnswer("");
    };

    recognition.onresult = (event: any) => {
      let text = "";

      for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
      ) {
        text += event.results[i][0].transcript;
      }

      setTranscript(text);

      const finalResult =
        event.results[event.results.length - 1].isFinal;

      if (finalResult && text.trim()) {
        askPakAssist(text.trim());
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setStatus("error");
    };

    recognition.onend = () => {
      setStatus((currentStatus) => {
        if (currentStatus === "listening") {
          return "idle";
        }

        return currentStatus;
      });
    };

    recognition.start();
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background: "#f5f7f5",
        fontFamily: "Arial",
        padding: "30px",
      }}
    >
      <div
        style={{
          width: "550px",
          padding: "30px",
          background: "white",
          borderRadius: "18px",
          textAlign: "center",
          boxShadow: "0 10px 30px rgba(0,0,0,0.08)",
        }}
      >
        <h1>PakAssist Voice</h1>

        <p>
          {status === "listening" && "Listening..."}

          {status === "thinking" &&
            "PakAssist is thinking..."}

          {status === "speaking" &&
            "PakAssist is speaking..."}

          {status === "idle" &&
            "Press the button and ask something"}

          {status === "error" &&
            "Something went wrong"}

          {status === "unsupported" &&
            "Speech recognition is not supported"}
        </p>

        <button
          onClick={startListening}
          disabled={
            status === "thinking" ||
            status === "speaking"
          }
          style={{
            padding: "14px 25px",
            border: "none",
            borderRadius: "10px",
            cursor:
              status === "thinking" ||
              status === "speaking"
                ? "not-allowed"
                : "pointer",
            fontSize: "16px",
          }}
        >
          {status === "listening"
            ? "🎙 Listening..."
            : "🎙 Speak"}
        </button>

        {transcript && (
          <div
            style={{
              marginTop: "25px",
              padding: "15px",
              background: "#f0f2f0",
              borderRadius: "10px",
              textAlign: "left",
            }}
          >
            <strong>You said:</strong>

            <p>{transcript}</p>
          </div>
        )}

        {answer && (
          <div
            style={{
              marginTop: "20px",
              padding: "15px",
              background: "#eef6ee",
              borderRadius: "10px",
              textAlign: "left",
            }}
          >
            <strong>PakAssist:</strong>

            <p
              style={{
                whiteSpace: "pre-wrap",
                lineHeight: "1.6",
              }}
            >
              {answer}
            </p>
          </div>
        )}

        {voiceAnswer && (
          <div
            style={{
              marginTop: "20px",
              padding: "15px",
              background: "#f4f4f4",
              borderRadius: "10px",
              textAlign: "left",
            }}
          >
            <strong>Voice version:</strong>

            <p
              style={{
                lineHeight: "1.6",
              }}
            >
              {voiceAnswer}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;