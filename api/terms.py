from pathlib import Path

def handler(event, context):
    """Vercel serverless function to serve Terms of Service page"""
    # Read the HTML file
    html_path = Path(__file__).parent / "templates" / "terms.html"

    if html_path.exists():
        html_content = html_path.read_text()
    else:
        html_content = "<h1>Terms of Service</h1><p>Coming soon</p>"

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html; charset=utf-8'
        },
        'body': html_content
    }
