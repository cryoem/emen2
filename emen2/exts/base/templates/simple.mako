<%inherit file="/page" />

% if ctxt.title:
    <h1>${ctxt.title}</h1>
% endif

${content or ''}