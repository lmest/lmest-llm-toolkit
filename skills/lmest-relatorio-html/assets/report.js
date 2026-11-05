// Equações: KaTeX substitui o MathML de reserva. Se uma falhar, o MathML continua no lugar e ela fica marcada.
if(window.katex)document.querySelectorAll('.tex').forEach(el=>{try{katex.render(el.dataset.tex,el,{displayMode:el.dataset.display==='1',throwOnError:true,strict:false,trust:c=>c.command==='\\htmlClass',macros:{'\\azul':'\\htmlClass{lm-eq-blue}{#1}','\\vermelho':'\\htmlClass{lm-eq-red}{#1}'}})}catch(e){el.classList.add('tex-falhou');console.warn('Equação não renderizada pelo KaTeX:',el.dataset.tex,e.message)}});
const dlg=document.querySelector('dialog'),big=dlg.querySelector('img');
document.querySelectorAll('.zoom').forEach(b=>b.addEventListener('click',()=>{const i=b.querySelector('img');big.src=i.src;big.alt=i.alt;dlg.showModal()}));
dlg.addEventListener('click',()=>dlg.close());
document.querySelectorAll('.fig-abas').forEach(f=>{const chips=[...f.querySelectorAll('.chip')],panes=[...f.querySelectorAll('.pane')];chips.forEach(c=>c.addEventListener('click',()=>{chips.forEach(o=>{const on=o===c;o.classList.toggle('lm-tab--on',on);o.setAttribute('aria-pressed',on)});panes.forEach(p=>p.hidden=p.dataset.p!==c.dataset.t)}))});
const links=[...document.querySelectorAll('nav a')],map=new Map(links.map(a=>[a.getAttribute('href').slice(1),a]));
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.remove('on'));map.get(e.target.id)?.classList.add('on')}}),{rootMargin:'-25% 0px -70% 0px'});
document.querySelectorAll('main section[id]').forEach(s=>io.observe(s));
