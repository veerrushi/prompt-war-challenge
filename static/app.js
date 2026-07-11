class RainReadyChat {
    constructor() {
        this.chatHistory = document.getElementById('chat-history');
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        
        this.messages = [];
        this.initEventListeners();
    }

    initEventListeners() {
        // Auto-resize textarea
        this.userInput.addEventListener('input', () => this.handleInputResize());

        // Handle Enter key (Shift+Enter for new line)
        this.userInput.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // Form submission
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    handleInputResize() {
        this.userInput.style.height = 'auto';
        this.userInput.style.height = `${this.userInput.scrollHeight}px`;
        if (this.userInput.value.trim() === '') {
            this.userInput.style.height = 'auto';
        }
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.chatForm.dispatchEvent(new Event('submit'));
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const content = this.userInput.value.trim();
        if (!content) return;

        // Add user message to UI and history
        this.appendMessage('user', content);
        this.messages.push({ role: 'user', content });
        
        this.resetInput();

        // Add empty assistant message container for streaming
        const { messageDiv, contentDiv } = this.createAssistantMessageContainer();
        this.chatHistory.appendChild(messageDiv);
        
        // Show initial loading state
        contentDiv.innerHTML = this.getLoadingIndicatorHTML();
        this.scrollToBottom();

        try {
            await this.streamResponse(contentDiv);
        } catch (error) {
            console.error('Chat error:', error);
            this.handleError(contentDiv, error);
        } finally {
            this.sendBtn.disabled = false;
            this.userInput.focus();
        }
    }

    resetInput() {
        this.userInput.value = '';
        this.userInput.style.height = 'auto';
        this.sendBtn.disabled = true;
    }

    createAssistantMessageContainer() {
        const messageDiv = this.createMessageElement('assistant');
        const contentDiv = messageDiv.querySelector('.message-content');
        return { messageDiv, contentDiv };
    }

    getLoadingIndicatorHTML() {
        return `
            <div class="loading-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        `;
    }

    async streamResponse(contentDiv) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ messages: this.messages })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error: ${response.status}`);
        }

        // Clear loading indicator
        contentDiv.innerHTML = '';
        
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
            this.scrollToBottom();
        }

        // Save full response to history
        this.messages.push({ role: 'assistant', content: fullResponse });
    }

    handleError(contentDiv, error) {
        contentDiv.innerHTML = `<span class="error-message">Error: ${error.message}. Please try again.</span>`;
        // Remove the last user message from state so they can try again
        this.messages.pop();
    }

    createMessageElement(role) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = `<div class="message-content"></div>`;
        return div;
    }

    appendMessage(role, content) {
        const div = this.createMessageElement(role);
        const contentDiv = div.querySelector('.message-content');
        
        if (role === 'assistant') {
            contentDiv.innerHTML = marked.parse(content);
        } else {
            // Escape user input to prevent XSS
            contentDiv.textContent = content;
        }
        
        this.chatHistory.appendChild(div);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatHistory.scrollTo({
            top: this.chatHistory.scrollHeight,
            behavior: 'smooth'
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new RainReadyChat();
});
