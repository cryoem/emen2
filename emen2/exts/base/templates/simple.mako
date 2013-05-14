<%inherit file="/page" />

% if ctxt.title:
    <h1>${ctxt.title}</h1>
% endif

<p>
${content or ''}
</p>