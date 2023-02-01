import jsonrpc.jsonutil
from xml.etree.ElementTree import ElementTree

import xml.etree.ElementTree as etree
import xml.dom.minidom

# e = etree.Element("test")    
# e.append(etree.Element("asd", lol="1"))
# print str(etree.tostring(e))


# print etree.tostring(e.find("/"))


recs = [
    {
        "name": "test",
        "keytype": "record",
        "groups": ["a", "b", "c"],
        "comments": [["root","2010","comment"], ["ianrees","2011","changed!"]],
        "history": [["root","20100101T00:00:00","abc", [1,2,3]], ["ianrees","20111010T10:10:10","xyz", "oldvalue"]]
    },
    {
        "name": "goodbye",
        "keytype": "record",
        "abc": [1,2,3],
        "subdict": {"sub1": 1, "sub2": 2}
    }
]



def enc(input):
    return jsonrpc.jsonutil.encode_(input)
    
    
    
def enc_xml(parent, k, v):
    # history, comments, permissions are nested and need to be handled specially.
    if k == "history":
        for v2 in v:
            elem = etree.Element("history", user=v2[0], datetime=v2[1])
            parent.append(elem)
            enc_xml(elem, v2[2], v2[3])
    
    elif k == "comments":
        for v2 in v:
            child = etree.Element("comments", user=v2[0], datetime=v2[1])
            child.text = v2[2]
            parent.append(child)
            
    elif hasattr(v, "items"):
        keytype = v.pop('keytype', None)
        name = v.pop('name', None)
        if keytype and name:
            # New element
            child = etree.Element(keytype, name=name)
            parent.append(child)
            parent = child

        for k2, v2 in v.items():
            child = etree.Element(k)
            parent.append(child)
            enc_xml(child, k2, v2)

    elif hasattr(v, "__iter__"):
        for v2 in v:
            if hasattr(v2, "__iter__"):
                child = etree.Element(k)
                parent.append(child)
                enc_xml(child, k, v2)
            else:
                enc_xml(parent, k, v2)

    else:
        elem = etree.Element(k)
        elem.text = str(v)
        parent.append(elem)
    
    
if __name__ == "__main__":
    elem = etree.Element("collection")

    d = enc_xml(elem, None, recs)

    pretty = etree.tostring(elem)
    pr2 = xml.dom.minidom.parseString(pretty)
    print pr2.toprettyxml()
