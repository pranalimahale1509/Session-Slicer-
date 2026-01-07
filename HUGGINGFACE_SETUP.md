# Hugging Face API Setup Guide

## Quick Start

1. **Get Your FREE API Key**:
   - Go to: https://huggingface.co/settings/tokens
   - Click "New token"
   - Give it a name (e.g., "SessionSlice")
   - Select "Read" access
   - Copy your token

2. **Add to SessionSlice**:
   - Open SessionSlice
   - Go to **Settings > AI Integration**
   - Paste your API key
   - Click "Save Key"

3. **Start Chatting**:
   - Go to **Buddy Chat**
   - Ask ANY question!
   - The AI will respond using Hugging Face's Mixtral-8x7B model

## Using .env File (Optional)

Create a `.env` file in the SessionSlice folder:

```
HUGGINGFACE_API_KEY=hf_your_token_here
HUGGINGFACE_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
```

## Features

- ✅ **100% FREE** - Hugging Face Inference API is free!
- ✅ **Powerful Model** - Uses Mixtral-8x7B (comparable to GPT-3.5)
- ✅ **No Rate Limits** - Much more generous than OpenAI free tier
- ✅ **Privacy Friendly** - Open source models
- ✅ **Offline Fallback** - Works without API key (limited features)

## Troubleshooting

**"Model is loading"**: The first request might take 20-30 seconds as the model loads. Just wait and try again.

**"Request failed"**: Check your API key is valid and you have internet connection.

**"Timeout"**: The model is still loading. Wait a minute and try again.
