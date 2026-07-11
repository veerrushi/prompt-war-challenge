document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // State to maintain conversation history
    let messages = [];

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if(this.value.trim() === '') {
            this.style.height = 'auto';
        }
    });

    // Handle Enter key (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const content = userInput.value.trim();
        if (!content) return;

        // 1. Add user message to UI
        appendMessage('user', content);
        messages.push({ role: 'user', content: content });
        
        // Reset input
        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        // 2. Add empty assistant message for streaming
        const assistantMsgDiv = createMessageContainer('assistant');
        const contentDiv = assistantMsgDiv.querySelector('.message-content');
        chatHistory.appendChild(assistantMsgDiv);
        
        // Show loading state initially
        contentDiv.innerHTML = `
            <div class="loading-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ messages: messages })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            // Clear loading indicator
            contentDiv.innerHTML = '';
            
            // Set up stream reading
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let fullResponse = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                fullResponse += chunk;
                
                // Parse markdown and update UI incrementally
                contentDiv.innerHTML = marked.parse(fullResponse);
                scrollToBottom();
            }

            // Save full response to history
            messages.push({ role: 'assistant', content: fullResponse });

        } catch (error) {
            console.error('Chat error:', error);
            contentDiv.innerHTML = `<span class="error-message">Error: ${error.message}. Please try again.</span>`;
            // Remove the last user message from state so they can try again if they want
            messages.pop();
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    });

    function createMessageContainer(role) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = `<div class="message-content"></div>`;
        return div;
    }

    function appendMessage(role, content) {
        const div = createMessageContainer(role);
        const contentDiv = div.querySelector('.message-content');
        
        if (role === 'assistant') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            // Escape user input to prevent XSS
            contentDiv.textContent = content;
        }
        
        chatHistory.appendChild(div);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: 'smooth'
        });
    }
});
