import '../App.css'; 
import React from 'react';

function Home() {
  return (
    <div className="container">
      <div className="body">
  
          
        <div className="main">
        <img src="./assets/profile_picture.png" alt="Rana Banankhah" style={{width: '150px', height: 'auto'}} />
          <h2> Hi, I'm Rana 👋 </h2>
          <p>I study Computer Science and Product Design at Stanford.</p>
          <h4>These are my life goals:</h4>

          <ol>
            <li>
              <strong>Explore as much as possible.</strong> Physical exploration (traveling, entering rooms I’m not supposed to be in) and conceptual exploration (learning new things, meeting new people) 

            </li>
            <li> <strong>Live Fully.</strong> Cram as much as I can into this one, precious life I have. Live 10 lives in one

            </li>
            <li> <strong>Live Freely.</strong> Financial freedom. Physical freedom. Freedom from social pressures. 
              </li>
            <li><strong>Laugh.</strong> A lot.</li> 
          </ol>
          <p> In my free time, I enjoy tinkering, <a href="https://www.goodreads.com/ranaba" target="_blank" rel="noopener noreferrer">reading,</a> writing, and <a href="https://www.ultimate-guitar.com/u/froggiewrld" target="_blank" rel="noopener noreferrer">playing guitar.</a> </p>

          
          
          <p>
          <b>Reach me:</b>
          <br />
            Twitter: <a href="https://twitter.com/ranabanankhah" target="_blank" rel="noopener noreferrer">@ranabanankhah</a>
            <br />
            Email: <a href="mailto:ranab@stanford.edu">ranab@stanford.edu </a> or  <a href="mailto:rbanankhah@gc-fellows.com">rbanankhah@gc-fellows.com  </a>
            <br />
          </p>
          <p style={{fontSize: '12px'}}>If you're reading this, you should check out my <a href="https://medium.com/finn-jackson/the-parable-of-the-taoist-farmer-8f52bba7f12c" target="_blank" rel="noopener noreferrer">favorite story</a>.</p>
        </div>
      </div>
    </div>
  );
}

export default Home;
