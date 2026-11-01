(()=>{const f=document.getElementById('brief-form');if(!f)return;const out=document.getElementById('brief-output'),status=document.getElementById('brief-status');f.addEventListener('submit',e=>{e.preventDefault();const v=id=>document.getElementById(id).value.trim();out.value=`${v('brief-type')}について相談したいです。

目的・使い道：${v('brief-purpose')||'相談して決めたいです'}
必要な点数・ページ数・長さ：
用意できる素材：
予算の上限（手数料等を含む）：${v('brief-budget')||'見積もりを見て相談したいです'}
希望納期：${v('brief-date')||'対応可能な日程を教えてください'}

確認したいこと：
・対応範囲と追加費用の条件
・修正回数と修正できる範囲
・納品形式と利用できる範囲
・初案と最終納品までの日程

この条件で相談・見積もりは可能でしょうか。`;status.textContent='相談文を作成しました。必要な項目を書き足してからお使いください。';out.focus();});document.getElementById('copy-brief').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(out.value);status.textContent='コピーしました。内容を確認してから相談にお使いください。';}catch{out.focus();out.select();status.textContent='相談文を選択しました。端末のコピー操作でコピーしてください。';}});})();
