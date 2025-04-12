"use client"

import { useState, useRef, useEffect } from "react"
import ChatHeader from "./chat-header"
import MessageList from "./message-list"
import ChatInput from "./chat-input"
import BeamsBackground from "../background/beams-background"
import { Mic, MicOff, HelpCircle } from "lucide-react"

export type Message = {
  id: string
  content: string
  sender: "user" | "bot"
  timestamp: Date
  originalContent?: string // To store the original content before translation
}

// Type for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
    speechSynthesis: SpeechSynthesis;
  }
}

// Function to translate text using a translation API
async function translateText(text: string, targetLang: string): Promise<string> {
  // If target language is English, no translation needed
  if (targetLang === 'en') {
    return text;
  }
  
  try {
    // We'll use the DeepL API here, but you can replace with Google Translate, Bhashini, etc.
    // Fallback to placeholder on API errors
    
    // In a real implementation, you'd make an API call like:
    /*
    const response = await fetch('https://api.deepl.com/v2/translate', {
      method: 'POST',
      headers: {
        'Authorization': `DeepL-Auth-Key ${process.env.DEEPL_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: [text],
        target_lang: targetLang.toUpperCase(),
      }),
    });
    
    const data = await response.json();
    return data.translations[0].text;
    */
    
    // For demonstration, let's use some placeholder translations for Hindi
    if (targetLang === 'hi' && text.includes('funds that match your query')) {
      return 'मैंने आपकी खोज से मेल खाने वाले ये फंड पाए हैं:';
    } else if (targetLang === 'hi' && text.includes('Ask me about mutual funds')) {
      return 'नमस्ते! मैं आपका फंड खोज सहायक हूं। मुझसे म्यूचुअल फंड या निवेश के बारे में पूछें!';
    } else if (targetLang === 'ta' && text.includes('funds that match your query')) {
      return 'உங்கள் தேடலுக்கு பொருந்தும் நிதிகளை கண்டுபிடித்தேன்:';
    }
    
    // Simple placeholder for demo - append language code to show it's "translated"
    return `[${targetLang}] ${text}`;
    
  } catch (error) {
    console.error('Translation error:', error);
    return text; // Return original text if translation fails
  }
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm your Fund Search Assistant. Ask me about mutual funds or investments!",
      sender: "bot",
      timestamp: new Date(),
    },
  ])
  const [isTyping, setIsTyping] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [language, setLanguage] = useState('en') // Default language is English
  const [showHelp, setShowHelp] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<any>(null)

  // Listen for language change events
  useEffect(() => {
    const handleLanguageChange = (event: CustomEvent) => {
      const newLanguage = event.detail;
      setLanguage(newLanguage);
      
      // Translate existing messages when language changes
      translateAllMessages(newLanguage);
    };
    
    window.addEventListener('language-change', handleLanguageChange as EventListener);
    
    return () => {
      window.removeEventListener('language-change', handleLanguageChange as EventListener);
    };
  }, [messages]);
  
  // Function to translate all existing messages
  const translateAllMessages = async (targetLang: string) => {
    if (targetLang === 'en') {
      // If switching to English, restore original messages if available
      setMessages(messages.map(msg => ({
        ...msg,
        content: msg.originalContent || msg.content,
      })));
      return;
    }
    
    const translatedMessages = await Promise.all(
      messages.map(async (msg) => {
        // Store original content if not already stored
        const originalContent = msg.originalContent || msg.content;
        
        // Translate the content
        const translatedContent = await translateText(originalContent, targetLang);
        
        return {
          ...msg,
          content: translatedContent,
          originalContent: originalContent,
        };
      })
    );
    
    setMessages(translatedMessages);
  };

  // Initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      
      // Set language for speech recognition based on selected language
      recognitionRef.current.lang = language === 'en' ? 'en-US' : 
                                  language === 'hi' ? 'hi-IN' : 
                                  language === 'ta' ? 'ta-IN' :
                                  language === 'te' ? 'te-IN' :
                                  language === 'kn' ? 'kn-IN' :
                                  language === 'mr' ? 'mr-IN' : 'en-US';
      
      recognitionRef.current.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        handleSendMessage(transcript);
      };
      
      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [language]); // Re-initialize when language changes

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.abort();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (error) {
        console.error('Could not start speech recognition', error);
      }
    }
  };

  // Text-to-speech function
  const speakResponse = (text: string) => {
    if ('speechSynthesis' in window) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Set language for speech synthesis
      utterance.lang = language === 'en' ? 'en-US' : 
                      language === 'hi' ? 'hi-IN' : 
                      language === 'ta' ? 'ta-IN' :
                      language === 'te' ? 'te-IN' :
                      language === 'kn' ? 'kn-IN' :
                      language === 'mr' ? 'mr-IN' : 'en-US';
                      
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleShowHelp = () => {
    setShowHelp(!showHelp);
    if (!showHelp) {
      // Add a help message
      const helpMessage: Message = {
        id: Date.now().toString(),
        content: 
          "💬 **Fund Search Assistant - Help**\n\n" +
          "**Search for Funds:**\n" +
          "- Ask about specific funds: \"Tell me about ICICI Prudential Technology Fund\"\n" +
          "- Search with keywords: \"Show me some equity funds\"\n\n" +
          "**Voice Input:**\n" +
          "- Click the microphone button to speak your query\n" +
          "- Wait for the red indicator, then speak clearly\n\n" +
          "**Language Support:**\n" +
          "- Change language using the dropdown in the header\n" +
          "- Responses will be translated to your selected language\n" +
          "- Voice recognition and speech will use your selected language\n\n" +
          "**Fund Explanations:**\n" +
          "- For detailed fund information, ask: \"Explain HDFC Top 100 Fund\"\n" +
          "- Get personalized recommendations: \"Which funds are good for retirement?\"",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, helpMessage]);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      sender: "user",
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Set typing indicator
    setIsTyping(true)
    
    try {
      // If not in English, translate the query to English for processing
      let processedContent = content;
      if (language !== 'en') {
        // In a real implementation, you would translate from the source language to English here
        // For demo purposes, we'll just use the original content
        // processedContent = await translateText(content, 'en'); 
      }
      
      // Call our fund-chat API
      const response = await fetch('/api/fund-chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            ...messages.map(m => ({
              role: m.sender === 'user' ? 'user' : 'assistant',
              content: m.originalContent || m.content
            })),
            { role: 'user', content: processedContent }
          ]
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get response');
      }
      
      const data = await response.json();
      let botResponse = data.response || "I'm having trouble finding information about that fund.";
      
      // Store original response before translation
      const originalContent = botResponse;
      
      // If not in English, translate the response
      if (language !== 'en') {
        botResponse = await translateText(botResponse, language);
      }
      
      // Add bot response
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: botResponse,
        sender: "bot",
        timestamp: new Date(),
        originalContent: originalContent // Store original content for language switching
      }
      
      setMessages((prev) => [...prev, botMessage]);
      
      // Speak the response if appropriate
      speakResponse(botResponse);
      
    } catch (error) {
      console.error('Error getting response:', error);
      
      // Fallback response
      const errorMessage = "I'm sorry, I encountered an error while processing your request.";
      const translatedError = language !== 'en' ? 
        await translateText(errorMessage, language) : errorMessage;
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: translatedError,
        sender: "bot",
        timestamp: new Date(),
        originalContent: errorMessage
      }
      
      setMessages((prev) => [...prev, botMessage]);
    } finally {
      setIsTyping(false);
    }
  }

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="fixed inset-0 h-screen w-full overflow-hidden">
      <BeamsBackground intensity="medium" />

      <div className="absolute inset-0 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-xl bg-black/40 backdrop-blur-xl border border-white/10 shadow-2xl overflow-hidden">
          <ChatHeader />
          <MessageList messages={messages} isTyping={isTyping} messagesEndRef={messagesEndRef} />
          <div className="border-t border-white/10 bg-black/50 p-3 flex items-center">
            <button 
              onClick={toggleListening}
              className={`p-2 rounded-full ${isListening ? 'bg-red-500' : 'bg-blue-500'} mr-2 flex items-center justify-center`}
              title={isListening ? "Stop listening" : "Start voice input"}
            >
              {isListening ? <MicOff className="h-5 w-5 text-white" /> : <Mic className="h-5 w-5 text-white" />}
            </button>
            <div className="flex-1">
              <ChatInput onSendMessage={handleSendMessage} />
            </div>
            <button
              onClick={handleShowHelp}
              className="p-2 rounded-full bg-gray-700/50 ml-2 flex items-center justify-center hover:bg-gray-600/50"
              title="Help"
            >
              <HelpCircle className="h-5 w-5 text-white" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

