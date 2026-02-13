"""Landing page template generator for validation experiments."""

from typing import Literal


class LandingPageGenerator:
    """Generate HTML landing page templates for opportunity validation."""

    @staticmethod
    def generate_problem_solution(
        title: str,
        problem: str,
        solution: str,
        features: list[str] | None = None,
        cta_text: str = "Join Waitlist",
    ) -> str:
        """Generate a problem-solution landing page.

        Args:
            title: Product title
            problem: Problem description
            solution: Solution description
            features: List of key features
            cta_text: Call-to-action button text

        Returns:
            HTML string for landing page
        """
        features_html = ""
        if features:
            features_items = "\n".join(
                f'          <li class="feature-item">✓ {feature}</li>' for feature in features
            )
            features_html = f"""
        <div class="features">
          <h2>Key Features</h2>
          <ul class="features-list">
{features_items}
          </ul>
        </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            font-size: 1.8rem;
            margin-bottom: 15px;
            color: #667eea;
        }}
        .section p {{
            font-size: 1.1rem;
            color: #555;
            line-height: 1.8;
        }}
        .features {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 8px;
            margin: 30px 0;
        }}
        .features-list {{
            list-style: none;
            padding: 0;
        }}
        .feature-item {{
            font-size: 1.1rem;
            padding: 10px 0;
            color: #333;
        }}
        .cta-section {{
            text-align: center;
            padding: 40px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .cta-section h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        .email-form {{
            display: flex;
            gap: 10px;
            max-width: 500px;
            margin: 0 auto;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .email-input {{
            flex: 1;
            min-width: 250px;
            padding: 15px 20px;
            font-size: 1rem;
            border: 2px solid #ddd;
            border-radius: 6px;
            outline: none;
        }}
        .email-input:focus {{
            border-color: #667eea;
        }}
        .cta-button {{
            padding: 15px 40px;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #777;
            font-size: 0.9rem;
        }}
        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            .section h2 {{
                font-size: 1.5rem;
            }}
            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
        </div>
        <div class="content">
            <div class="section">
                <h2>The Problem</h2>
                <p>{problem}</p>
            </div>
            <div class="section">
                <h2>Our Solution</h2>
                <p>{solution}</p>
            </div>
{features_html}
            <div class="cta-section">
                <h2>Be the First to Know</h2>
                <p style="margin-bottom: 20px;">Join our waitlist and get early access when we launch.</p>
                <form class="email-form" onsubmit="return handleSubmit(event)">
                    <input type="email" class="email-input" placeholder="Enter your email" required id="emailInput">
                    <button type="submit" class="cta-button">{cta_text}</button>
                </form>
                <p id="successMessage" style="display: none; color: #28a745; margin-top: 15px; font-weight: 600;">Thanks! We'll be in touch soon.</p>
            </div>
        </div>
        <div class="footer">
            <p>This is a validation experiment. No spam, ever.</p>
        </div>
    </div>
    <script>
        function handleSubmit(event) {{
            event.preventDefault();
            const email = document.getElementById('emailInput').value;
            // Store in localStorage for tracking
            const signups = JSON.parse(localStorage.getItem('signups') || '[]');
            signups.push({{ email: email, timestamp: new Date().toISOString() }});
            localStorage.setItem('signups', JSON.stringify(signups));
            // Show success message
            document.getElementById('successMessage').style.display = 'block';
            document.getElementById('emailInput').value = '';
            // Optional: Send to analytics or backend
            console.log('Signup:', email);
            return false;
        }}
    </script>
</body>
</html>"""

    @staticmethod
    def generate_waitlist(
        title: str,
        tagline: str,
        description: str,
        value_props: list[str] | None = None,
    ) -> str:
        """Generate a simple waitlist landing page.

        Args:
            title: Product title
            tagline: Short tagline
            description: Product description
            value_props: List of value propositions

        Returns:
            HTML string for landing page
        """
        value_props_html = ""
        if value_props:
            props_items = "\n".join(
                f'              <div class="value-prop">✓ {prop}</div>' for prop in value_props
            )
            value_props_html = f"""
            <div class="value-props">
{props_items}
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Join the Waitlist</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f172a;
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            text-align: center;
        }}
        .logo {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }}
        .tagline {{
            font-size: 1.5rem;
            color: #94a3b8;
            margin-bottom: 30px;
        }}
        .description {{
            font-size: 1.1rem;
            color: #cbd5e1;
            line-height: 1.8;
            margin-bottom: 40px;
        }}
        .value-props {{
            margin-bottom: 40px;
        }}
        .value-prop {{
            font-size: 1.1rem;
            color: #e2e8f0;
            padding: 10px 0;
        }}
        .waitlist-form {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .email-input {{
            flex: 1;
            min-width: 250px;
            padding: 15px 20px;
            font-size: 1rem;
            background: #1e293b;
            border: 2px solid #334155;
            border-radius: 8px;
            color: white;
            outline: none;
        }}
        .email-input:focus {{
            border-color: #667eea;
        }}
        .submit-button {{
            padding: 15px 40px;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .submit-button:hover {{
            transform: translateY(-2px);
        }}
        .success-message {{
            display: none;
            color: #34d399;
            font-weight: 600;
            margin-top: 15px;
        }}
        .counter {{
            margin-top: 30px;
            color: #64748b;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">{title}</div>
        <div class="tagline">{tagline}</div>
        <div class="description">{description}</div>
{value_props_html}
        <form class="waitlist-form" onsubmit="return handleWaitlistSignup(event)">
            <input type="email" class="email-input" placeholder="Enter your email" required id="emailInput">
            <button type="submit" class="submit-button">Join Waitlist</button>
        </form>
        <div class="success-message" id="successMessage">You're on the list! We'll be in touch soon.</div>
        <div class="counter" id="counter"></div>
    </div>
    <script>
        function handleWaitlistSignup(event) {{
            event.preventDefault();
            const email = document.getElementById('emailInput').value;
            const signups = JSON.parse(localStorage.getItem('waitlist_signups') || '[]');
            signups.push({{ email: email, timestamp: new Date().toISOString() }});
            localStorage.setItem('waitlist_signups', JSON.stringify(signups));
            document.getElementById('successMessage').style.display = 'block';
            document.getElementById('emailInput').value = '';
            updateCounter();
            return false;
        }}
        function updateCounter() {{
            const signups = JSON.parse(localStorage.getItem('waitlist_signups') || '[]');
            if (signups.length > 0) {{
                document.getElementById('counter').textContent = signups.length + ' people have joined the waitlist';
            }}
        }}
        updateCounter();
    </script>
</body>
</html>"""

    @staticmethod
    def generate_feature_vote(
        title: str,
        description: str,
        features: list[dict[str, str]],
    ) -> str:
        """Generate a feature voting landing page.

        Args:
            title: Product title
            description: Product description
            features: List of features with 'name' and 'description' keys

        Returns:
            HTML string for landing page
        """
        feature_items = "\n".join(
            f"""            <div class="feature-card" data-feature="{feature.get('name', '')}">
                <h3>{feature.get('name', 'Feature')}</h3>
                <p>{feature.get('description', '')}</p>
                <button class="vote-button" onclick="voteFeature('{feature.get('name', '')}')">Vote for this</button>
                <span class="vote-count" id="votes-{feature.get('name', '').replace(' ', '-')}">0 votes</span>
            </div>"""
            for feature in features
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Vote on Features</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 2.5rem;
            color: #333;
            margin-bottom: 10px;
        }}
        .header p {{
            font-size: 1.2rem;
            color: #666;
        }}
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .feature-card {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .feature-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        .feature-card h3 {{
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 10px;
        }}
        .feature-card p {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 20px;
        }}
        .vote-button {{
            width: 100%;
            padding: 12px;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .vote-button:hover {{
            opacity: 0.9;
        }}
        .vote-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        .vote-count {{
            display: block;
            text-align: center;
            margin-top: 10px;
            color: #667eea;
            font-weight: 600;
        }}
        .email-section {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .email-section h2 {{
            margin-bottom: 15px;
            color: #333;
        }}
        .email-form {{
            display: flex;
            gap: 10px;
            max-width: 500px;
            margin: 20px auto 0;
            flex-wrap: wrap;
            justify-content: center;
        }}
        .email-input {{
            flex: 1;
            min-width: 250px;
            padding: 12px 20px;
            font-size: 1rem;
            border: 2px solid #ddd;
            border-radius: 6px;
            outline: none;
        }}
        .email-input:focus {{
            border-color: #667eea;
        }}
        .submit-button {{
            padding: 12px 30px;
            font-size: 1rem;
            font-weight: 600;
            color: white;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }}
        .success-message {{
            display: none;
            color: #28a745;
            margin-top: 15px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{description}</p>
            <p style="margin-top: 10px; color: #888;">Vote for the features you want most!</p>
        </div>
        <div class="features-grid">
{feature_items}
        </div>
        <div class="email-section">
            <h2>Get Early Access</h2>
            <p>Leave your email to be notified when we build your favorite features.</p>
            <form class="email-form" onsubmit="return handleEmailSubmit(event)">
                <input type="email" class="email-input" placeholder="Enter your email" required id="emailInput">
                <button type="submit" class="submit-button">Notify Me</button>
            </form>
            <div class="success-message" id="successMessage">Thanks! We'll keep you posted.</div>
        </div>
    </div>
    <script>
        function voteFeature(featureName) {{
            const votes = JSON.parse(localStorage.getItem('feature_votes') || '{{}}');
            votes[featureName] = (votes[featureName] || 0) + 1;
            localStorage.setItem('feature_votes', JSON.stringify(votes));
            updateVoteCounts();
            // Disable button after voting
            event.target.disabled = true;
            event.target.textContent = 'Voted!';
        }}
        function updateVoteCounts() {{
            const votes = JSON.parse(localStorage.getItem('feature_votes') || '{{}}');
            for (const [feature, count] of Object.entries(votes)) {{
                const id = 'votes-' + feature.replace(/ /g, '-');
                const element = document.getElementById(id);
                if (element) {{
                    element.textContent = count + ' vote' + (count !== 1 ? 's' : '');
                }}
            }}
        }}
        function handleEmailSubmit(event) {{
            event.preventDefault();
            const email = document.getElementById('emailInput').value;
            const signups = JSON.parse(localStorage.getItem('feature_vote_emails') || '[]');
            signups.push({{ email: email, timestamp: new Date().toISOString() }});
            localStorage.setItem('feature_vote_emails', JSON.stringify(signups));
            document.getElementById('successMessage').style.display = 'block';
            document.getElementById('emailInput').value = '';
            return false;
        }}
        updateVoteCounts();
    </script>
</body>
</html>"""

    @classmethod
    def generate(
        cls,
        template_type: Literal["problem_solution", "waitlist", "feature_vote"],
        **kwargs,
    ) -> str:
        """Generate a landing page based on template type.

        Args:
            template_type: Type of template to generate
            **kwargs: Template-specific arguments

        Returns:
            HTML string for landing page

        Raises:
            ValueError: If template_type is not recognized
        """
        if template_type == "problem_solution":
            return cls.generate_problem_solution(**kwargs)
        elif template_type == "waitlist":
            return cls.generate_waitlist(**kwargs)
        elif template_type == "feature_vote":
            return cls.generate_feature_vote(**kwargs)
        else:
            raise ValueError(f"Unknown template type: {template_type}")
