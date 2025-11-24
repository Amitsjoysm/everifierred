import React from 'react';
import { Helmet } from 'react-helmet-async';

const SEO = ({
  title = 'MailGuard - Professional Email Verification Service',
  description = 'Verify email addresses in real-time with MailGuard. Reduce bounce rates, improve deliverability, and protect your sender reputation with our advanced email verification API.',
  keywords = 'email verification, email validation, email checker, verify email, email deliverability, bounce rate reduction, email list cleaning, SMTP verification',
  canonicalUrl = 'https://service-restarter.preview.emergentagent.com',
  ogImage = 'https://service-restarter.preview.emergentagent.com/og-image.png',
  ogType = 'website',
  twitterCard = 'summary_large_image',
  author = 'MailGuard Team',
  structuredData = null,
  noindex = false,
}) => {
  const fullTitle = title.includes('MailGuard') ? title : `${title} | MailGuard`;
  
  return (
    <Helmet>
      {/* Primary Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="title" content={fullTitle} />
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content={author} />
      <link rel="canonical" href={canonicalUrl} />
      
      {/* Robots */}
      {noindex && <meta name="robots" content="noindex, nofollow" />}
      {!noindex && <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />}
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content={ogType} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:site_name" content="MailGuard" />
      <meta property="og:locale" content="en_US" />
      
      {/* Twitter */}
      <meta name="twitter:card" content={twitterCard} />
      <meta name="twitter:url" content={canonicalUrl} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
      <meta name="twitter:creator" content="@MailGuard" />
      
      {/* Additional SEO Tags */}
      <meta name="language" content="English" />
      <meta name="revisit-after" content="7 days" />
      <meta name="coverage" content="Worldwide" />
      <meta name="distribution" content="Global" />
      <meta name="rating" content="General" />
      <meta httpEquiv="Content-Type" content="text/html; charset=utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      
      {/* Structured Data */}
      {structuredData && (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      )}
    </Helmet>
  );
};

export default SEO;
