def capitalize(tag, reverse = False):
    if not reverse:
        return tag.capitalize()
    else:
        return tag[0].lower() + tag[1:]
        
        