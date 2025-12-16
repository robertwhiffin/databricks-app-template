import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { FaPaperPlane, FaRobot, FaUser } from 'react-icons/fa'
import './App.css'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatResponse {
  session_id: string
  messages: Array<{
    role: string
    content: string
    timestamp: string
  }>
  response: string
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          session_id: sessionId
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ChatResponse = await response.json()

      // Update session ID if this is first message
      if (!sessionId && data.session_id) {
        setSessionId(data.session_id)
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
      // Focus back on input
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const startNewChat = () => {
    setMessages([])
    setSessionId(null)
    setInput('')
    inputRef.current?.focus()
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <FaRobot className="header-icon" />
            <h1>Databricks Chat App</h1>
          </div>
          {messages.length > 0 && (
            <button onClick={startNewChat} className="new-chat-button">
              New Chat
            </button>
          )}
        </div>
      </header>

      {/* Messages */}
      <main className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-screen">
            <FaRobot className="welcome-icon" />
            <h2>Welcome to Databricks Chat</h2>
            <p>Start a conversation by typing a message below</p>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-icon">
                  {message.role === 'user' ? <FaUser /> : <FaRobot />}
                </div>
                <div className="message-content">
                  {message.role === 'assistant' ? (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <p>{message.content}</p>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-icon">
                  <FaRobot />
                </div>
                <div className="message-content">
                  <div className="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input */}
      <footer className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here... (Shift+Enter for new line)"
            className="message-input"
            rows={1}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="send-button"
            aria-label="Send message"
          >
            <FaPaperPlane />
          </button>
        </div>
      </footer>
    </div>
  )
}

export default App
