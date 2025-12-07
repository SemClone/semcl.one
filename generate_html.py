#!/usr/bin/env python3
"""
Generate index.html from component data
"""
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

# Import the components data from update_readme
from update_readme import fetch_github_stats, fetch_pypi_stats, parse_github_url, calculate_completion

def fetch_download_stats(valid_packages: List[str]) -> Tuple[Optional[int], Dict[str, int]]:
    """Fetch download statistics from status.semcl.one and return total organic downloads and per-package stats

    Args:
        valid_packages: List of PyPI package names to include in the total count
    """
    try:
        url = "https://status.semcl.one/data/stats.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())

        total_downloads = 0
        package_downloads = {}

        # Iterate through all packages in stats.json
        if 'packages' in data:
            for package_name, package_data in data['packages'].items():
                if isinstance(package_data, dict) and 'recent' in package_data:
                    recent = package_data['recent']
                    if 'data' in recent and 'last_month_without_mirrors' in recent['data']:
                        # Get organic downloads (without_mirrors)
                        downloads = recent['data']['last_month_without_mirrors']
                        package_downloads[package_name] = downloads
                        # Only count downloads for packages in our components list
                        if package_name in valid_packages:
                            total_downloads += downloads

        return (total_downloads if total_downloads > 0 else None, package_downloads)

    except Exception as e:
        print(f"⚠️  Warning: Could not fetch download stats: {e}")
        import traceback
        traceback.print_exc()
        return (None, {})

def format_download_count(count: int) -> str:
    """Format download count in K+ format"""
    if count >= 1000:
        return f"{count / 1000:.1f}K+".replace('.0K+', 'K+')
    return str(count)

def fetch_rss_news(limit: int = 3) -> List[Dict[str, str]]:
    """Fetch latest news from RSS feed"""
    try:
        url = "https://community.semcl.one/feed.xml"
        with urllib.request.urlopen(url, timeout=10) as response:
            xml_content = response.read().decode('utf-8')

        root = ET.fromstring(xml_content)
        channel = root.find('channel')
        if not channel:
            return []

        news_items = []
        for item in channel.findall('item')[:limit]:
            title_elem = item.find('title')
            link_elem = item.find('link')
            desc_elem = item.find('description')
            date_elem = item.find('pubDate')

            if title_elem is not None and link_elem is not None:
                # Extract image from description if present
                image_url = None
                description = ""
                if desc_elem is not None and desc_elem.text:
                    desc_text = desc_elem.text
                    # Try to extract image URL from CDATA
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', desc_text)
                    if img_match:
                        image_url = img_match.group(1)
                    # Extract text content, removing HTML and truncating
                    text_content = re.sub(r'<[^>]+>', '', desc_text)
                    description = ' '.join(text_content.split()[:20]) + '...'

                # Parse and format date
                date_str = ""
                if date_elem is not None and date_elem.text:
                    try:
                        # Parse RSS date format: "Wed, 04 Dec 2025 00:00:00 +0000"
                        date_obj = datetime.strptime(date_elem.text, '%a, %d %b %Y %H:%M:%S %z')
                        date_str = date_obj.strftime('%B %d, %Y')
                    except:
                        date_str = date_elem.text

                news_items.append({
                    'title': title_elem.text,
                    'link': link_elem.text,
                    'description': description,
                    'image': image_url,
                    'date': date_str
                })

        return news_items

    except Exception as e:
        print(f"⚠️  Warning: Could not fetch RSS feed: {e}")
        return []

def generate_html():
    """Generate index.html with updated component stats"""
    
    # Define all components (same as in update_readme.py)
    components = [
        {
            'name': 'Frontend UI',
            'component_id': 'semantic-copycat-frontend',
            'github': 'https://github.com/oscarvalenzuelab/semantic-copycat-frontend',
            'pypi': None,
            'description': 'Web interface for scan submission and results visualization',
            'category': 'Web Platform',
            'license': 'MIT'
        },
        {
            'name': 'Backend API', 
            'component_id': 'semantic-copycat-backend',
            'github': 'https://github.com/oscarvalenzuelab/semantic-copycat-backend',
            'pypi': None,
            'description': 'Core API services with scan queue management and orchestration',
            'category': 'Web Platform',
            'license': 'MIT'
        },
        {
            'name': 'PURL to Source',
            'component_id': 'purl2src',
            'github': 'https://github.com/SemClone/purl2src',
            'pypi': 'purl2src',
            'description': 'Downloads source code from Package URLs (npm, PyPI, Maven, etc.)',
            'category': 'Analysis Pipeline',
            'license': 'MIT',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'Semantic CopycatM',
            'component_id': 'semantic-copycat-miner',
            'github': None,
            'pypi': None,
            'description': 'Extracts code patterns and performs initial license detection',
            'category': 'Analysis Pipeline',
            'status_override': 'complete',
            'version_override': '1.7.0',
            'license': 'Private Beta'
        },
        {
            'name': 'Binary Sniffer',
            'component_id': 'binarysniffer',
            'github': 'https://github.com/SemClone/binarysniffer',
            'pypi': 'binarysniffer',
            'description': 'Identifies hidden OSS components embedded in binary files',
            'category': 'Analysis Pipeline',
            'license': 'MIT',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'Open Agentic Framework',
            'component_id': 'open-agentic-framework',
            'github': 'https://github.com/oscarvalenzuelab/open_agentic_framework',
            'pypi': None,
            'description': 'Agentic analysis framework for intelligent code pattern detection',
            'category': 'Analysis Pipeline',
            'license': 'Apache-2.0',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'OSS License ID Library',
            'component_id': 'semantic-copycat-oslili',
            'github': 'https://github.com/SemClone/osslili',
            'pypi': 'osslili',
            'description': 'High-performance license detection across 700+ SPDX identifiers with confidence scores',
            'category': 'License Analysis',
            'license': 'Apache-2.0',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'PURL to Notices',
            'component_id': 'semantic-copycat-purl2notice',
            'github': 'https://github.com/SemClone/purl2notices',
            'pypi': 'purl2notices',
            'description': 'Generates legal notices with licenses and copyright information',
            'category': 'License Analysis',
            'license': 'MIT',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'OSS Notices',
            'component_id': 'ossnotices',
            'github': 'https://github.com/SemClone/ossnotices',
            'pypi': 'ossnotices',
            'description': 'Simplified CLI wrapper for generating open source legal notices',
            'category': 'License Analysis',
            'license': 'MIT',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'SCMA',
            'component_id': 'semantic-copycat-ccda',
            'github': 'https://github.com/oscarvalenzuelab/semantic-copycat-ccda',
            'pypi': None,
            'description': 'SEMCL Advisory - Evolution of OSSA Scanner for semantic code copycat detection and advisory generation',
            'category': 'License Analysis',
            'license': 'MIT'
        },
        {
            'name': 'UPMEX',
            'component_id': 'semantic-copycat-upmex',
            'github': 'https://github.com/SemClone/upmex',
            'pypi': 'upmex',
            'description': 'Universal package metadata extractor supporting 13 package ecosystems',
            'category': 'Analysis Pipeline',
            'license': 'MIT',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'Source to PURL',
            'component_id': 'src2purl',
            'github': 'https://github.com/SemClone/src2purl',
            'pypi': 'src2purl',
            'description': 'Identifies package coordinates from source code using SWHIDs and multiple strategies',
            'category': 'Analysis Pipeline',
            'license': 'AGPL-3.0',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'VulnQ',
            'component_id': 'vulnq',
            'github': 'https://github.com/SemClone/vulnq',
            'pypi': 'vulnq',
            'description': 'Lightweight, multi-source vulnerability query tool that consolidates security data from OSV.dev, GitHub Advisory, and NIST NVD using PURLs, CPE strings, and file hashes',
            'category': 'Risk Analysis',
            'license': 'Apache-2.0',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'OSPAC',
            'component_id': 'ospac',
            'github': 'https://github.com/SemClone/ospac',
            'pypi': 'ospac',
            'description': 'Open Source Policy as Code - policy engine with declarative, data-driven compliance logic defined in versionable policy files',
            'category': 'Analysis Pipeline',
            'license': 'Apache-2.0',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'MCP-SemClone',
            'component_id': 'mcp-semclone',
            'github': 'https://github.com/SemClone/mcp-semclone',
            'pypi': 'mcp-semclone',
            'description': 'Model Context Protocol server providing comprehensive OSS compliance and vulnerability analysis capabilities through the SEMCL.ONE toolchain',
            'category': 'Integration Tools',
            'license': 'Apache-2.0',
            'status_override': 'complete',
            'completion_override': 100.0
        },
        {
            'name': 'OSSVal',
            'component_id': 'ossval',
            'github': 'https://github.com/SemClone/ossval',
            'pypi': 'ossval',
            'description': 'Calculate the development cost savings from using open source software by analyzing SBOMs or package lists using COCOMO II models',
            'category': 'Risk Analysis',
            'license': 'Apache-2.0',
            'status_override': 'complete',
            'completion_override': 100.0
        }
    ]
    
    # Fetch stats for all components
    component_stats = []
    total_components_ready = 0
    
    for component in components:
        stats = {
            'name': component['name'],
            'component_id': component['component_id'],
            'description': component['description'],
            'category': component.get('category', 'Core'),
            'license': component.get('license', 'TBD'),
            'github_exists': False,
            'pypi_exists': False,
            'version': component.get('version_override', '0.0.0'),
            'open_issues': 0,
            'closed_issues': 0,
            'total_issues': 0,
            'completion': 0.0,
            'github_url': component.get('github', ''),
            'pypi_url': f"https://pypi.org/project/{component['pypi']}/" if component.get('pypi') else None,
            'status_override': component.get('status_override', None)
        }
        
        # Fetch GitHub stats
        if component.get('github'):
            parsed = parse_github_url(component['github'])
            if parsed:
                owner, repo = parsed
                github_stats = fetch_github_stats(owner, repo)
                if github_stats:
                    stats['github_exists'] = github_stats.get('exists', False)
                    stats['open_issues'] = github_stats.get('open_issues', 0)
                    stats['closed_issues'] = github_stats.get('closed_issues', 0)
                    stats['total_issues'] = github_stats.get('total_issues', 0)
                    stats['version'] = github_stats.get('latest_version', '0.0.0')
                    
                    if component.get('completion_override') is None:
                        if stats['total_issues'] > 0:
                            stats['completion'] = calculate_completion(stats['closed_issues'], stats['total_issues'])
                        elif stats['github_exists'] and stats['version'] != '0.0.0':
                            stats['completion'] = 100.0
                        elif stats['github_exists']:
                            stats['completion'] = 10.0
        
        # Fetch PyPI stats if applicable
        if component.get('pypi'):
            pypi_stats = fetch_pypi_stats(component['pypi'])
            if pypi_stats:
                stats['pypi_exists'] = pypi_stats.get('exists', False)
                if pypi_stats.get('version', '0.0.0') != '0.0.0':
                    stats['version'] = pypi_stats['version']
                    if stats['completion'] == 0.0 and stats['pypi_exists']:
                        stats['completion'] = 100.0
        
        # Handle manual status overrides
        if stats['status_override'] == 'complete':
            stats['completion'] = component.get('completion_override', 100.0)
            stats['github_exists'] = True
            if component.get('version_override'):
                stats['version'] = component['version_override']
        elif stats['status_override'] == 'functional':
            stats['completion'] = component.get('completion_override', 80.0)
            stats['github_exists'] = True
            if component.get('version_override'):
                stats['version'] = component['version_override']
        
        # Count ready components
        if stats['version'] != '0.0.0' or stats['github_exists'] or stats['status_override'] in ['complete', 'functional']:
            total_components_ready += 1
        
        component_stats.append(stats)
    
    # Calculate overall completion
    overall_completion = (total_components_ready / len(components)) * 100

    # Get list of valid PyPI package names from components
    valid_pypi_packages = [c['pypi'] for c in components if c.get('pypi')]

    # Fetch download stats (only for packages in our components list)
    total_downloads, package_downloads = fetch_download_stats(valid_pypi_packages)
    downloads_display = format_download_count(total_downloads) if total_downloads else "N/A"

    # Read existing HTML as template
    with open('index.html', 'r') as f:
        html_content = f.read()

    # Update the overall progress - look for stat-number instead of stat-value
    html_content = re.sub(
        r'<div class="stat-number">\d+\.?\d*%</div>',
        f'<div class="stat-number">{overall_completion:.0f}%</div>',
        html_content,
        count=1
    )

    # Update component count
    html_content = re.sub(
        r'(<div class="stat-card">\s*<div class="stat-number">)\d+(</div>\s*<div class="stat-label">Components</div>)',
        f'\\g<1>{len(components)}\\g<2>',
        html_content,
        flags=re.DOTALL
    )

    # Update downloads count
    html_content = re.sub(
        r'(<div class="stat-card">\s*<div class="stat-number">)[^<]+(</div>\s*<div class="stat-label">Downloads</div>)',
        f'\\g<1>{downloads_display}\\g<2>',
        html_content,
        flags=re.DOTALL
    )

    # Sort components: Ready components first, then In Dev components
    # We need to create tuples of (component, stats) to keep them paired
    component_pairs = list(zip(components, component_stats))

    def sort_key(pair):
        _, stats = pair
        is_ready = (stats['version'] != '0.0.0' or
                   stats.get('status_override') in ['complete', 'functional'] or
                   stats['completion'] >= 80.0)
        # Return 0 for ready (first), 1 for in dev (last)
        return 0 if is_ready else 1

    component_pairs.sort(key=sort_key)

    # Generate component cards HTML
    component_cards_html = ""
    for component, stats in component_pairs:
        is_ready = (stats['version'] != '0.0.0' or
                   stats.get('status_override') in ['complete', 'functional'] or
                   stats['completion'] >= 80.0)

        status_class = "status-ready" if is_ready else "status-development"
        status_text = "Ready" if is_ready else "In Dev"

        # Get package name for downloads lookup (component is already available from the loop)
        package_name = component.get('pypi', '')
        downloads = package_downloads.get(package_name, 0) if package_name else 0

        # Build the metadata and links line (all inline)
        # Format: vX.X.X | License | <icons> Downloads
        metadata_parts = []

        # Only show version if it's not 0.0.0
        if stats['version'] != '0.0.0':
            metadata_parts.append(f"v{stats['version']}")

        # Always show license
        metadata_parts.append(stats['license'])

        # Build inline links and downloads
        links_inline = []
        if stats['github_url']:
            if stats['github_exists'] or stats.get('status_override') == 'complete':
                links_inline.append(f'<a href="{stats["github_url"]}" title="GitHub" target="_blank" rel="noopener noreferrer"><i class="fab fa-github"></i></a>')
        if stats['pypi_url'] and stats['pypi_exists']:
            links_inline.append(f'<a href="{stats["pypi_url"]}" title="PyPI" target="_blank" rel="noopener noreferrer"><i class="fab fa-python"></i></a>')

        # Add downloads if available
        if stats['version'] != '0.0.0' and downloads > 0:
            links_inline.append(f'{format_download_count(downloads)} Downloads')

        # Combine everything into one line
        metadata_str = " | ".join(metadata_parts)
        if links_inline:
            metadata_str += " | " + " ".join(links_inline)

        component_cards_html += f"""                <div class="component-card">
                    <div class="component-header">
                        <span class="component-name">{stats['name']}</span>
                        <span class="component-status {status_class}">{status_text}</span>
                    </div>
                    <div class="component-meta">{metadata_str}</div>
                    <p class="component-desc" style="margin-top: 1rem;">{stats['description']}</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {stats['completion']:.0f}%"></div>
                    </div>
                </div>

"""
    
    # Find and replace the components section
    pattern = r'(<div class="component-grid">)(.*?)(</div>\s*</section>)'
    replacement = f'\\1\n{component_cards_html}            \\3'
    html_content = re.sub(pattern, replacement, html_content, flags=re.DOTALL)

    # Fetch and generate news section
    news_items = fetch_rss_news(limit=3)
    news_html = ""
    if news_items:
        for news in news_items:
            image_html = ""
            if news['image']:
                image_html = f"""                        <div class="news-image">
                            <a href="{news['link']}" target="_blank">
                                <img src="{news['image']}" alt="{news['title']}">
                            </a>
                        </div>
"""
            news_html += f"""                    <div class="news-card">
{image_html}                        <div class="news-content">
                            <h3 class="news-title">
                                <a href="{news['link']}" target="_blank">{news['title']}</a>
                            </h3>
                            <p class="news-desc">{news['description']}</p>
                            <div class="news-date">{news['date']}</div>
                        </div>
                    </div>

"""

    # Replace news section with updated content
    news_pattern = r'<section id="news"[^>]*>.*?</section>\s*'
    news_section = f"""<section id="news" class="container">
        <div class="news-grid">
{news_html}        </div>
    </section>

"""
    html_content = re.sub(news_pattern, news_section, html_content, flags=re.DOTALL)

    # Update the last updated timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    html_content = re.sub(
        r'Last updated: [^<]+',
        f'Last updated: {timestamp}',
        html_content
    )
    
    # Write updated HTML
    with open('index.html', 'w') as f:
        f.write(html_content)

    print(f"✅ index.html updated successfully!")
    print(f"📊 Overall completion: {overall_completion:.0f}%")
    print(f"🎯 Components: {len(components)} total, {total_components_ready} ready")
    print(f"📥 Downloads (last month, organic): {downloads_display}")

if __name__ == "__main__":
    generate_html()