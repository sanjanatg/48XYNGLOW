import { NextResponse } from 'next/server';

// Function to determine if query is fund-related
function isFundQuery(query: string): boolean {
  const fundKeywords = [
    'fund', 'invest', 'mutual', 'etf', 'security', 'securities', 'stock',
    'equity', 'debt', 'icici', 'hdfc', 'sbi', 'axis', 'kotak', 'aditya',
    'birla', 'nippon', 'tata', 'uti', 'growth', 'dividend', 'nav', 'return',
    'portfolio', 'asset', 'allocation', 'risk', 'market', 'cap', 'scheme',
    'expense', 'ratio', 'investment'
  ];
  
  return fundKeywords.some(keyword => 
    query.toLowerCase().includes(keyword.toLowerCase())
  );
}

// Function to determine if the query is asking for an explanation
function isExplanationQuery(query: string): boolean {
  const explainKeywords = [
    'explain', 'details', 'more about', 'tell me about', 'what is', 
    'how does', 'suitable', 'risk', 'good for', 'recommend',
    'information on', 'details on', 'explain about', 'description'
  ];
  
  // Check if it contains explanation keywords
  const containsExplainKeyword = explainKeywords.some(keyword => 
    query.toLowerCase().includes(keyword.toLowerCase())
  );
  
  // Check if it likely mentions a specific fund
  const mentionsSpecificFund = query.includes('fund') || 
    query.includes('ICICI') || query.includes('SBI') || 
    query.includes('HDFC') || query.includes('Aditya') || 
    query.includes('Kotak');
  
  return containsExplainKeyword && mentionsSpecificFund;
}

// Function to extract fund name from an explanation query
function extractFundNameFromQuery(query: string): string | null {
  // Basic extraction logic - can be enhanced with NLP
  const words = query.split(/\s+/);
  
  // Common fund houses
  const fundHouses = ['icici', 'hdfc', 'sbi', 'axis', 'kotak', 'aditya', 'birla', 'nippon', 'tata', 'uti'];
  
  // Look for fund house names as starting points
  for (const house of fundHouses) {
    if (query.toLowerCase().includes(house)) {
      // Get the position of the fund house
      const houseIndex = query.toLowerCase().indexOf(house);
      
      // Extract a reasonable window after the fund house (up to 5 words)
      const remaining = query.substring(houseIndex);
      const potentialName = remaining.split(/\s+/).slice(0, 5).join(' ');
      
      return potentialName.trim();
    }
  }
  
  // If no fund house found but "fund" is mentioned
  if (query.toLowerCase().includes('fund')) {
    // Find the word "fund" and include a few words before it
    const fundIndex = query.toLowerCase().indexOf('fund');
    const start = Math.max(0, query.substring(0, fundIndex).lastIndexOf(' ', fundIndex - 15));
    return query.substring(start, fundIndex + 4).trim();
  }
  
  return null;
}

// Function to handle fund explanations
async function handleFundExplanation(query: string): Promise<string> {
  try {
    // Extract potential fund name
    const fundName = extractFundNameFromQuery(query);
    
    if (!fundName) {
      return "I'd be happy to explain a specific fund to you. Could you mention which fund you're interested in?";
    }
    
    // Extract user context if available (could be investment goals, risk profile)
    let userContext = null;
    if (query.toLowerCase().includes('for retirement') || 
        query.toLowerCase().includes('retire')) {
      userContext = "Planning for retirement";
    } else if (query.toLowerCase().includes('long term') || 
               query.toLowerCase().includes('long-term')) {
      userContext = "Long-term investment goals";
    } else if (query.toLowerCase().includes('short term') || 
               query.toLowerCase().includes('short-term')) {
      userContext = "Short-term investment goals";
    } else if (query.toLowerCase().includes('safe') || 
               query.toLowerCase().includes('low risk')) {
      userContext = "Conservative investor with low risk tolerance";
    } else if (query.toLowerCase().includes('high return') || 
               query.toLowerCase().includes('aggressive')) {
      userContext = "Aggressive investor seeking high returns";
    }
    
    // Call the fund explanation API
    const explainResponse = await fetch('http://localhost:8000/explain', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        fund_name: fundName,
        user_context: userContext
      }),
    });
    
    if (!explainResponse.ok) {
      throw new Error('Explanation failed');
    }
    
    const explainResult = await explainResponse.json();
    
    // Format the explanation response
    let response = `**${explainResult.fund_name}**\n\n`;
    response += explainResult.explanation;
    
    if (explainResult.risk_level) {
      response += `\n\n**Risk Level**: ${explainResult.risk_level}`;
    }
    
    response += `\n\nWould you like to know about any other funds or have specific questions about ${explainResult.fund_name}?`;
    
    return response;
    
  } catch (error) {
    console.error('Fund explanation error:', error);
    return "I'm sorry, I couldn't retrieve an explanation for that fund. Could you try again with the complete fund name?";
  }
}

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();
    
    // Validate input
    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Invalid request format' },
        { status: 400 }
      );
    }
    
    // Get the latest user message
    const latestUserMessage = messages
      .filter((m: any) => m.role === 'user')
      .pop()?.content || '';
    
    // Check if it's an explanation query
    if (isExplanationQuery(latestUserMessage)) {
      try {
        const explanation = await handleFundExplanation(latestUserMessage);
        return NextResponse.json({ response: explanation });
      } catch (error) {
        console.error('Explanation handling error:', error);
        // Fall through to regular fund search if explanation fails
      }
    }
    
    // Determine if it's a fund-related query
    if (isFundQuery(latestUserMessage)) {
      // Call our Python fund search API
      try {
        // Assume the FastAPI server is running on port 8000
        const searchResponse = await fetch('http://localhost:8000/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: latestUserMessage,
            top_k: 5,
            search_type: 'hybrid'
          }),
        });
        
        if (!searchResponse.ok) {
          throw new Error('Fund search failed');
        }
        
        const searchResults = await searchResponse.json();
        
        // Format the fund search results into a nice response
        let response = 'I found these funds that match your query:\n\n';
        
        searchResults.results.forEach((fund: any, index: number) => {
          response += `${index + 1}. ${fund.fund_name}\n`;
          response += `   Fund House: ${fund.fund_house || 'N/A'}\n`;
          response += `   Category: ${fund.category || 'N/A'}\n`;
          if (fund.sub_category) {
            response += `   Sub-Category: ${fund.sub_category}\n`;
          }
          if (fund.combined_score) {
            response += `   Match Score: ${(fund.combined_score * 100).toFixed(1)}%\n`;
          }
          response += '\n';
        });
        
        response += `Would you like me to explain any of these funds in detail?`;
        
        return NextResponse.json({ response });
      } catch (error) {
        console.error('Fund search error:', error);
        // Fall back to DeepSeek if fund search fails
      }
    }
    
    // For non-fund queries or when fund search fails, use DeepSeek
    const apiKey = process.env.DEEPSEEK_API_KEY;
    if (!apiKey) {
      return NextResponse.json(
        { error: 'API key not configured' },
        { status: 500 }
      );
    }
    
    // Add system prompt to guide DeepSeek
    const enhancedMessages = [
      {
        role: 'system',
        content: `You are a financial advisor assistant specialized in mutual funds and investments.
        Focus on providing helpful information about investment options, funds, and financial advice.
        If asked about specific Indian mutual funds that you don't have information about,
        suggest that the user can search for them using this chat interface.`
      },
      ...messages
    ];
    
    const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: enhancedMessages,
        temperature: 0.7,
        max_tokens: 1000,
        stream: false,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.error?.message || 'Failed to get response from DeepSeek' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json({
      response: data.choices[0].message.content
    });
    
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      { response: "I'm sorry, I encountered an error while processing your request. Please try again." },
      { status: 200 }  // Return 200 with error message to show in UI
    );
  }
} 