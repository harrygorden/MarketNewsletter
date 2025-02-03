import os
import logging
import anvil.secrets

from openai import OpenAI

def chunk_newsletter(newsletter_content):
    # For demonstration purposes, assume the newsletter is small enough to not require chunking
    return [newsletter_content]

def analyze_newsletter_chunk(chunk, is_final=False):
    # Replace with real analysis logic as needed
    # For now, simply return a dummy analysis of the chunk
    analysis_excerpt = chunk[:100] + '...' if len(chunk) > 100 else chunk
    return {'status': 'success', 'analysis': f'Analysis of chunk: {analysis_excerpt}'}

def count_tokens(prompt):
    # Simplistic token count: number of words
    return len(prompt.split())

def analyze_email(newsletter_content: str) -> dict:
    try:
        # Create OpenAI client using API key from Anvil secrets
        client = OpenAI(api_key=anvil.secrets.get_secret('openai_api_key'))

        # Split newsletter into manageable chunks
        chunks = chunk_newsletter(newsletter_content)

        if len(chunks) == 1:
            return analyze_newsletter_chunk(chunks[0])

        # Analyze each chunk
        intermediate_analyses = []
        for i, chunk in enumerate(chunks):
            is_final = (i == len(chunks) - 1)
            result = analyze_newsletter_chunk(chunk, is_final)
            if result.get('status') == 'error':
                return result
            intermediate_analyses.append(result.get('analysis', ''))

        # If multiple chunks, combine the analyses
        if len(intermediate_analyses) > 1:
            combined_analysis = "\n\n".join(intermediate_analyses)
            final_prompt = f"""Based on the following combined analyses of the newsletter sections, provide a cohesive final analysis and trading plan:
\n\n{combined_analysis}\n\nPlease structure the final response in our standard format:
1. **Key Market Insights**
2. **Potential Trading Opportunities**
3. **Risk Factors to Consider**
4. **Recommended Trading Plan**
5. **Support and Resistance Levels**"""

            final_tokens = count_tokens(final_prompt)
            logging.info(f"Final analysis prompt tokens: {final_tokens}")

            if final_tokens > 6000:
                logging.warning("Final analysis too long, truncating intermediate analyses")
                shortened_analyses = [analysis[:1500] for analysis in intermediate_analyses]
                combined_analysis = "\n\n".join(shortened_analyses)
                final_prompt = f"""Based on the following summarized analyses of the newsletter sections, provide a cohesive final analysis and trading plan:
\n\n{combined_analysis}\n\nPlease structure the final response in our standard format:
1. **Key Market Insights**
2. **Potential Trading Opportunities**
3. **Risk Factors to Consider**
4. **Recommended Trading Plan**
5. **Support and Resistance Levels**"""

            # Make the final API call to combine all analyses
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional market analyst providing clear, actionable insights."},
                    {"role": "user", "content": final_prompt}
                ]
            )
            
            return {
                'status': 'success',
                'analysis': response.choices[0].message.content
            }
            
        return {
            'status': 'success',
            'analysis': intermediate_analyses[-1]
        }
        
    except Exception as e:
        logging.error(f"Error in analyze_email: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
