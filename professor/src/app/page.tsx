"use client";

import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css"; // Default styles

export default function CopilotKitPage() {
  return (
    <main className="h-screen w-screen dark">
      <div
        className="flex justify-center items-center h-full w-full bg-gray-900"
        data-testid="background-container"
      >
        <div className="h-full w-full rounded-lg">
          <CopilotChat
            className="h-full rounded-2xl mx-auto"
            labels={{ initial: "Hi, I'm an agent. Want to chat?" }}
          />
        </div>
      </div>
    </main>
  );
}