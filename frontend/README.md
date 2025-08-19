# ModularChatBot Frontend

A modern React-based frontend for the ModularChatBot system, built with Next.js, TypeScript, and Tailwind CSS.

## Features

- **Real-time Chat Interface**: Clean, modern chat UI with message bubbles
- **Multi-Conversation Support**: Sidebar for managing multiple conversations
- **Agent Visualization**: Shows which AI agent handled each response
- **Workflow Display**: Visual representation of agent routing decisions
- **Responsive Design**: Works on desktop and mobile devices
- **TypeScript**: Full type safety throughout the application
- **Modern UI**: Built with Tailwind CSS and shadcn/ui components

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Icons**: Lucide React
- **State Management**: React Hooks
- **API Client**: Custom fetch-based client

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Update `.env.local` with your API URL:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── globals.css      # Global styles
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main chat page
│   ├── components/          # React components
│   │   ├── ui/              # Reusable UI components
│   │   └── chat/            # Chat-specific components
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utility functions and API client
│   └── types/               # TypeScript type definitions
├── public/                  # Static assets
├── package.json             # Dependencies and scripts
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── next.config.js          # Next.js configuration
```

## API Integration

The frontend communicates with the backend through the following endpoints:

- `POST /chat` - Send chat messages
- `GET /conversations/user/{user_id}` - Get user conversations
- `POST /conversations` - Create new conversation
- `PUT /conversations/{id}/title` - Update conversation title
- `DELETE /conversations/{id}` - Delete conversation

## Components

### Core Components

- **ChatPage**: Main chat interface
- **ConversationSidebar**: Manages conversation list
- **MessageBubble**: Displays individual messages
- **ChatInput**: Message input and send functionality
- **LoadingMessage**: Loading state indicator

### UI Components

- **Button**: Reusable button component with variants
- **Input**: Form input component
- **Card**: Container component
- **Badge**: Status and label component
- **ScrollArea**: Custom scrollable area

## Customization

### Styling

The application uses Tailwind CSS with a custom design system. Colors and styling can be modified in:

- `tailwind.config.js` - Theme configuration
- `src/app/globals.css` - CSS variables and base styles

### Adding New Agents

To support new AI agents:

1. Update the `getAgentColor` function in `MessageBubble.tsx`
2. Add agent types to the API types in `src/types/api.ts`
3. Update the workflow display logic if needed

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

### Code Style

The project uses:
- ESLint for code linting
- Prettier for code formatting
- TypeScript for type safety

## Docker

The frontend can be run in Docker:

```bash
# Build the image
docker build -t modular-chatbot-frontend .

# Run the container
docker run -p 3000:3000 modular-chatbot-frontend
```

Or use the provided docker-compose.yml in the root directory:

```bash
docker-compose up frontend
```

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Test your changes thoroughly
4. Update documentation as needed

## License

This project is part of the ModularChatBot system.
