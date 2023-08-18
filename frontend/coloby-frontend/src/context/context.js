import React, {createContext, useState} from "react";

export const Context = createContext()

const ContextProvider = (props)=>{

const coloby = 'coloby'
    return(
        <Context.Provider value={{
                coloby
        }}>
            {props.children}
        </Context.Provider>
    )
}

export default ContextProvider