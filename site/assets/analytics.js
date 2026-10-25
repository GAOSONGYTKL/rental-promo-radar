(function () {
  'use strict';
  var id = 'G-1L8EC4RRZZ';
  function start() {
    if (window.rdrAnalyticsStarted) return;
    window.rdrAnalyticsStarted = true;
    window.dataLayer = window.dataLayer || [];
    function gtag(){window.dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', id, {allow_google_signals:false, allow_ad_personalization_signals:false});
    var s=document.createElement('script'); s.async=true;
    s.src='https://www.googletagmanager.com/gtag/js?id='+id;
    document.head.appendChild(s);
  }
  var choice; try {choice=localStorage.getItem('rdr-analytics-consent');} catch(e){}
  if(choice==='granted'){start();return;}
  if(choice==='denied')return;
  var box=document.createElement('aside');box.className='analytics-choice';
  box.setAttribute('aria-label','Optional analytics');
  box.innerHTML='<p>Allow optional Google Analytics cookies to help us understand site visits? <a href="/privacy/">Privacy details</a></p><button type="button" data-choice="granted">Allow analytics</button> <button type="button" data-choice="denied">Reject analytics</button>';
  box.addEventListener('click',function(e){var c=e.target.getAttribute('data-choice');if(!c)return;try{localStorage.setItem('rdr-analytics-consent',c);}catch(e){}box.remove();if(c==='granted')start();});
  document.body.appendChild(box);
})();
